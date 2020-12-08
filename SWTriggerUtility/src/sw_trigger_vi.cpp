// Copyright (c) 2020 Intel Corporation.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

/**
 * @file
 * @brief Software Trigger Utility for VideoIngestion
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
#include <unistd.h>

#include <eis/msgbus/msgbus.h>
#include <eis/msgbus/msg_envelope.h>
#include <eis/utils/logger.h>
#include <eis/utils/json_config.h>
#include <eis/utils/config.h>
#include "eis/config_manager/config_mgr.hpp"


#define SLEEP_DURATION_SECONDS 120
#define START_INGESTION_STR "START_INGESTION"
#define STOP_INGESTION_STR "STOP_INGESTION"
#define SNAPSHOT_STR "SNAPSHOT"
#define CLIENT "client"
#define REPLY_PAYLOAD "reply_payload"
#define STATUS "status_code"

#define FREE_MEMORY(msg_env) { \
    if (msg_env != NULL) { \
        msgbus_msg_envelope_destroy(msg_env); \
        msg_env = NULL; \
    } \
}

using namespace eis::config_manager;

enum SwTrigger {
        START_INGESTION,
        STOP_INGESTION,
        SNAPSHOT
    };

enum ReqStatusCode {
    REQUEST_HONORED = 0,
    REQUEST_NOT_HONORED,
    REQUEST_ALREADY_RUNNING,
    REQUEST_ALREADY_STOPPED,
    REQUEST_COMMAND_NOT_REGISTERED
};

void usage(const char* name) {
        std::cout <<name<<" usage: \n\n \
                    ./sw_trigger_vi [Duration to ingest in seconds] [<START_INGESTION | STOP_INGESTION>] [Config file path] \n\n \
                    -> Optional argument: START_INGESTION | STOP_INGESTION - Action to send to Video Ingestion service  \n \
                    -> Optional argument: Duration to ingest in seconds (default=120 seconds). \n \
                    -> Optional argument: SNAPSHOT - Action to send to Video Ingestion service to get frame snapshot. \n\n \
                    NOTE: As a prerequisite update the config.json file for sw_trigger_utility based on the config need. \n \
                    Refer README.md for more details on each options\n" << std::endl;

        std::cout <<" Examples:\n \
                                1. ./sw_trigger_utility\n \
                                2. ./sw_trigger_utility 300\n \
                                3. ./sw_trigger_utility START_INGESTION\n \
                                4. ./sw_trigger_utility STOP_INGESTION\n \
                                5. ./sw_trigger_utility SNAPSHOT" \
        << std::endl;
    }

// utility function
bool is_number(std::string s) {
    for (int i = 0; i < s.length(); i++) {
        if (isdigit(s[i]) == false) {
            return false;
        }
    }
    return true;
}

class SwTriggerUtility {
    private:
        const char* m_json_config_file;
        void* m_msgbus_ctx;
        recv_ctx_t* m_service_ctx;
        int m_duration;
        int m_log_level;
        size_t m_num_of_cycles;

    public:
        void read_etcd_config(config_t* app_config) {

            // log_level
            config_value_t* log_level_cvt = get_config_value(app_config->cfg,
                                                            "log_level");
            if (log_level_cvt == NULL) {
                const char* err = "\"log_level\" key is missing, setting to default log level as debug";
                LOG_WARN("%s", err);
                m_log_level = 3; // Since, we are not exiting, setting default to continue
            } else {
                m_log_level = log_level_cvt->body.integer;
            }

            //num_of_cycles
            config_value_t* num_of_cyles_cvt = get_config_value(app_config->cfg,
                                                               "num_of_cycles");

            if (num_of_cyles_cvt == NULL) {
                const char* err = "\"num_of_cyles\" key is missing, setting to default (1 cycle)";
                LOG_WARN("%s", err);
                m_num_of_cycles = 1;
            } else {
                m_num_of_cycles = num_of_cyles_cvt->body.integer;
            }

        }

        /**
        * Constructor
        * Constructor of SwTriggerUtility class
        */

        SwTriggerUtility(char* config_file_path) {
            try {
                // Initialize default values
                m_msgbus_ctx = NULL;
                m_service_ctx = NULL;

                m_duration = SLEEP_DURATION_SECONDS;
                // Set log level
                set_log_level((log_lvl_t)m_log_level);

                const char* dev_mode = getenv("DEV_MODE");
                if (dev_mode == NULL) {
                    throw "\"DEV_MODE\" env not set";
                }

                if (strncmp(dev_mode, "TRUE", 5) == 0) {
                    setenv("DEV_MODE", "", 1);
                    setenv("CONFIGMGR_CERT", "", 1);
                    setenv("CONFIGMGR_KEY", "", 1);
                    setenv("CONFIGMGR_CACERT", "", 1);
                }

                // Since VI is the server & sw_trigger_utility is the client, it is impersonating as VideoAnalytics to
                // get access to the allowed_clients list in VI.
                ConfigMgr* ch = new ConfigMgr();
                AppCfg* cfg = ch->getAppConfig();
                if(cfg == NULL) {
                    const char* err = "Failed to initialize AppCfg object";
                    throw("%s", err);
                }
                config_t* app_config = cfg->getConfig();
                if (app_config == NULL) {
                    const char* err =  "AppConfig is missing";
                    throw("%s", err);
                }

                read_etcd_config(app_config);

                char* interface_name = getenv("interface_name");
                if (interface_name == NULL) {
                    // Defaulting to the name default if env not set
                    interface_name = "default";
                }
                ClientCfg* client_ctx = ch->getClientByName(interface_name);
                config_t* config = client_ctx->getMsgBusConfig();

                config_value_t* interface_value = client_ctx->getInterfaceValue("Name");
                if (interface_value->type != CVT_STRING) {
                    const char* err = "Interface value type is not a string";
                    LOG_ERROR("%s", err);
                    exit(1);
                }
                char* name = interface_value->body.string;
                LOG_INFO("Interface value is: %s", name);

                m_msgbus_ctx = msgbus_initialize(config);
                if (m_msgbus_ctx == NULL) {
                    const char* err = "Failed to initialize message bus";
                    LOG_ERROR("%s", err);
                    throw err;
                }

                msgbus_ret_t ret = msgbus_service_get(
                m_msgbus_ctx, name, NULL, &m_service_ctx);
                if (ret != MSG_SUCCESS) {
                    const char* err = "Failed to initialize service, msgbus_service_get failed";
                    LOG_ERROR("%s", err);
                    throw err;
                }

            }
            catch (std::exception& ex) {
                LOG_ERROR("Exception = %s occurred in construction of SW_trigger_utility object ", ex.what());
                exit(1);
            } catch(const char *err) {
                LOG_ERROR("Exception occurred: %s", err);
                exit(1);
            }
        }

        ~SwTriggerUtility() {
            if (m_service_ctx != NULL)
                msgbus_recv_ctx_destroy(m_msgbus_ctx, m_service_ctx);
            if (m_msgbus_ctx != NULL)
                msgbus_destroy(m_msgbus_ctx);
        }

        /**
        * Function to receive the Acknowledgemnt from VI (Server) to the client
        * "SW_TRigger_utility if the "Request (Start/stop ingestion) has been honored or not.""
        * */
        void recv_ack() {
            msg_envelope_t* msg = NULL;
            try {
                LOG_INFO_0("Waiting for ack");
                msgbus_ret_t ret = msgbus_recv_wait(m_msgbus_ctx, m_service_ctx, &msg);
                if (ret != MSG_SUCCESS) {
                    // Interrupt is an acceptable error
                    const char* err = "";
                    if (ret != MSG_ERR_EINTR)
                        err = "Interrupt received. Failed to receive SW trigger ACK";
                    else
                    err = "Failed to receive SW trigger ACK";
                    throw err;
                    LOG_ERROR("%s", err);
                }
                LOG_INFO_0("received ack");
                msg_envelope_elem_body_t* ack_env;
                ret = msgbus_msg_envelope_get(msg, REPLY_PAYLOAD, &ack_env);
                if (ret != MSG_SUCCESS) {
                    const char* err = "Failed to receive ACK from server for the sw_trigger";
                    LOG_ERROR("%s", err);
                    throw(err);
                }

                if (MSG_ENV_DT_OBJECT != ack_env->type) {
                    const char* err = "ACK received from server for the sw_trigger has a wrong data type";
                    LOG_ERROR("%s", err);
                    throw(err);
                }
                LOG_INFO_0("After reading the reply_payload");
                msg_envelope_elem_body_t* env_status = msgbus_msg_envelope_elem_object_get(
                        ack_env, STATUS);
                if (env_status == NULL) {
                    throw("object corresponding to the status key in reply_payload is null");
                }
                int status = env_status->body.integer;
                LOG_INFO_0("After reading the REPLY STATUS");
                if (status == REQUEST_HONORED) {
                    LOG_INFO_0("REQUEST HONORED ");
                } else if (status == REQUEST_NOT_HONORED) {
                    LOG_INFO_0("REQUEST NOT HONORED ");
                } else if (status == REQUEST_ALREADY_RUNNING) {
                    LOG_INFO_0("DUPLICATE REQUEST SENT BY CLIENT, AS INGESTION IS ALREADY RUNNING");
                } else if(status == REQUEST_ALREADY_STOPPED) {
                    LOG_INFO_0("DUPLICATE REQUEST SENT BY CLIENT, AS INGESTION IS ALREADY STOPPED");
                } else if (status == REQUEST_COMMAND_NOT_REGISTERED) {
                    LOG_INFO_0("COMMAND IS NOT REGISTERED WITH COMMAND HANDLER, (Check if the command for example \"SW_Trigger\") is enabled in the config or not");
                } else {
                    LOG_ERROR_0("Received improper ack message. Exiting..");
                }
                FREE_MEMORY(msg);
            } catch(std::exception& ex) {
                LOG_ERROR("Exeption : %s occured during receving ACK from VI ", ex.what());
                FREE_MEMORY(msg);
                exit(1);
            } catch(const char *err) {
                LOG_ERROR("Exception occurred: %s", err);
                FREE_MEMORY(msg);
                exit(1);
            }
        }

        /**
        * Function to send the SW trigger from this utility to EIS VI app
        * to START_INGESTION/STOP_INGESTION.
        * @param: trig - Enum to decide what type of SW trigger is to be sent based on user's
        *  selection in commandline interface.
        * */
        void send_sw_trigger(SwTrigger trig) {
            msgbus_ret_t ret;
            msg_envelope_t* msg = NULL;
            try {
                switch (trig) {
                    case START_INGESTION: {
                        LOG_INFO_0("Sending START_INGESTION SW trigger..");
                        // form the JSON payload to be sent over the msgbus in a msg-envelope
                        msg_envelope_elem_body_t* sw_trigger = msgbus_msg_envelope_new_string(START_INGESTION_STR);
                        msg = msgbus_msg_envelope_new(CT_JSON);
                        ret = msgbus_msg_envelope_put(msg, "command", sw_trigger);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "Failed to put the payload message into message envelope";
                            LOG_ERROR("%s", err);
                            FREE_MEMORY(msg);
                            throw err;
                        }
                        LOG_INFO_0("Success putting payload into env");
                        LOG_INFO_0("Sending START_INGESTION sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- START_INGESTION";
                            LOG_ERROR("%s", err);
                            throw err;
                        }

                    }
                    break;
                    case STOP_INGESTION: {
                        LOG_INFO_0("Sending STOP_INGESTION SW trigger..");
                        // Form the JSON payload to be sent over the msgbus in a msg-envelope
                        msg_envelope_elem_body_t* sw_trigger = msgbus_msg_envelope_new_string(STOP_INGESTION_STR);
                        msg = msgbus_msg_envelope_new(CT_JSON);
                        ret = msgbus_msg_envelope_put(msg, "command", sw_trigger);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "Failed to put the payload message into message envelope";
                            LOG_ERROR("%s", err);
                            FREE_MEMORY(msg);
                            throw err;
                        }
                        LOG_INFO_0("Success putting payload into env");
                        LOG_INFO_0("Sending STOP_INGESTION sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- STOP_INGESTION";
                            LOG_ERROR("%s", err);
                            throw err;
                        }
                    }
                    break;
                    case SNAPSHOT: {
                        LOG_INFO_0("Sending SNAPSHOT SW trigger..");
                        // form the JSON payload to be sent over the msgbus in a msg-envelope
                        msg_envelope_elem_body_t* sw_trigger = msgbus_msg_envelope_new_string(SNAPSHOT_STR);
                        msg = msgbus_msg_envelope_new(CT_JSON);
                        ret = msgbus_msg_envelope_put(msg, "command", sw_trigger);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "Failed to put the payload message into message envelope";
                            LOG_ERROR("%s", err);
                            FREE_MEMORY(msg);
                            throw err;
                        }
                        LOG_INFO_0("Success putting payload into env");
                        LOG_INFO_0("Sending SNAPSHOT sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- SNAPSHOT";
                            LOG_ERROR("%s", err);
                            throw err;
                        }

                    }
                    break;

                    default: {
                        usage("sw_trigger_utility");
                    }
                    FREE_MEMORY(msg);
                };
            } catch(std::exception& ex) {
                LOG_ERROR("Exception: %s occured while sending software trigger ", ex.what());
                FREE_MEMORY(msg);
                exit(1);
            } catch(const char *err) {
                LOG_ERROR("Exception occurred: %s", err);
                FREE_MEMORY(msg);
                exit(1);
            }
        }

        void set_duration(int dur) {
            m_duration = dur;
        }

        /**
        * Function to perform the cycle of "START_INGESTION"->"Allow ingestion to happen for someime" -> "STOP_INGESTION"
        *
        * */
        void perform_full_cycle() {
            size_t count = m_num_of_cycles;
            while ( count > 0 ) {
                send_sw_trigger(START_INGESTION);
                recv_ack();
                sleep(m_duration);
                send_sw_trigger(STOP_INGESTION);
                recv_ack();
                sleep(m_duration);
                --count;
            }
        }

};


int main(int argc, char **argv) {
    try {
        SwTriggerUtility* sw_trigger_obj = NULL;
        if (argc > 3 ) {
            usage(argv[0]);
            return -1;
        }

        sw_trigger_obj = new SwTriggerUtility(argv[2]);

        switch (argc) {
            case 2: case 3: {
                // checking if the second arguement is the config json file, if yes then go to case 1
                if((std::string(argv[1]).find("json", 0)) != std::string::npos){
                    goto case_one;
                }
                if (!strcmp(argv[1], "START_INGESTION")) {
                    sw_trigger_obj->send_sw_trigger(START_INGESTION);
                    sw_trigger_obj->recv_ack();
                } else if (!strcmp(argv[1], "STOP_INGESTION")) {
                    sw_trigger_obj->send_sw_trigger(STOP_INGESTION);
                    sw_trigger_obj->recv_ack();
                } else if (!strcmp(argv[1], "SNAPSHOT")) {
                    sw_trigger_obj->send_sw_trigger(SNAPSHOT);
                    sw_trigger_obj->recv_ack();
                } else if (is_number(std::string(argv[1]))) {
                    sw_trigger_obj->set_duration(std::stoi(std::string(argv[1])));
                    sw_trigger_obj->perform_full_cycle();
                } else {
                    LOG_ERROR_0("ERROR: Provide proper commandline args");
                    usage(argv[0]);
                }
            }
            break;
            case 1: {
                case_one:
                sw_trigger_obj->perform_full_cycle();
            }
            break;
            default: {
                    LOG_ERROR_0("ERROR: Provide proper commandline args");
                    usage(argv[0]);
            }
        };
    } catch(std::exception &ex) {
        LOG_ERROR("exception in main of sw-trigger--utility: %s", ex.what());
    }
    return 0;
}
