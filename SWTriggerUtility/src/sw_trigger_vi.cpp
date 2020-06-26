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
#include <eis/config_manager/config_manager.h>
#include <eis/config_manager/env_config.h>


#define CONFIG_FILE_PATH "../config/config.json"

#define SLEEP_DURATION_SECONDS 120
#define START_INGESTION_STR "START_INGESTION"
#define STOP_INGESTION_STR "STOP_INGESTION"
#define CLIENT "client"
#define REPLY_PAYLOAD "reply_payload"
#define STATUS "status_code"

#define FREE_MEMORY(msg_env) { \
    if (msg_env != NULL) { \
        msgbus_msg_envelope_destroy(msg_env); \
        msg_env = NULL; \
    } \
}

enum SwTrigger {
        START_INGESTION,
        STOP_INGESTION
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
                    -> Optional argument: ../config/config.json - Configuration file used for sw_trigger_vi utility. \n\n\
                    NOTE: As a prerequisite update the config.json file for sw_trigger_utility based on the config need. \n \
                    Refer READMe.md for more details on each options\n" << std::endl;

        std::cout <<" Examples:\n \
                                1. ./sw_trigger_utility or ./sw_trigger_utility ../config/config.json\n \
                                2. ./sw_trigger_utility 300 or ./sw_trigger_utility 300 ../config/config.json\n \
                                3. ./sw_trigger_utility START_INGESTION or ./sw_trigger_utility START_INGESTION ../config/config.json\n \
                                4. ./sw_trigger_utility STOP_INGESTION or ./sw_trigger_utility STOP_INGESTION ../config/config.json" \
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
        config_mgr_t* m_config_mgr;
        env_config_t* m_env_config_client;

        // config file values
        std::string m_client_cfg;
        int m_log_level;
        size_t m_num_of_cycles;
        char* m_request_ep;
        char* m_request_ep_cfg;
        bool m_dev_mode;
        char* m_app_name;
        char* m_cert_file;
        char* m_key_file;
        char* m_trust_file;
        char* m_client;

    public:
        void read_config(char* config_file_path) {
            // parse config file
            config_t* config_file_cfg = json_config_new(config_file_path);
            if (config_file_cfg == NULL) {
                const char* err = "Failed to load JSON configuration of sw trigger utility";
                LOG_ERROR("%s", err);
                throw err;
            }

            // log_level
            config_value_t* log_level_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "log_level");
            if (log_level_cvt == NULL) {
                const char* err = "\"log_level\" key is missing, setting to default log level as debug";
                LOG_WARN("%s", err);
                m_log_level = 3; // Since, we are not exiting, setting default to continue
            } else {
                m_log_level = log_level_cvt->body.integer;
            }

            //num_of_cycles
            config_value_t* num_of_cyles_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "num_of_cycles");

            if (num_of_cyles_cvt == NULL) {
                const char* err = "\"num_of_cyles\" key is missing, setting to default (1 cycle)";
                LOG_WARN("%s", err);
                m_num_of_cycles = 1;
            } else {
                m_num_of_cycles = num_of_cyles_cvt->body.integer;
            }

            // RequestEP
            config_value_t* request_ep_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "RequestEP");
            if (request_ep_cvt == NULL) {
                const char* err = "\"RequestEP\" key is missing. Improper Configuration. ";
                LOG_ERROR("%s", err);
                throw err;
            } else {
                m_request_ep = request_ep_cvt->body.string;
            }

            m_client_cfg = std::string(m_request_ep) + "_cfg";

            // RequestEP's configuration (_cfg)
            config_value_t* request_ep_cfg_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              m_client_cfg.c_str());
            if (request_ep_cfg_cvt == NULL) {
                const char* err = "Request_EP's _cfg key is missing, Improper Configuration.";
                LOG_ERROR("%s", err);
                throw err;
            } else {
                m_request_ep_cfg = request_ep_cfg_cvt->body.string;
            }

            // dev_mode
            config_value_t* dev_mode_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "dev_mode");
            if ( dev_mode_cvt == NULL ) {
                const char* err = "dev_mode key is missing, Improper Configuration.";
                LOG_ERROR("%s", err);
                throw err;

            } else {
                m_dev_mode = dev_mode_cvt->body.boolean;
            }

            config_value_t* app_name_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "app_name");
            if (app_name_cvt == NULL) {
                const char* err = "\"app_name\" key is missing, setting to default";
                LOG_WARN("%s", err);
                m_app_name = "VideoAnalytics";
            } else {
                m_app_name = app_name_cvt->body.string;
            }

            // Only if prod mode then read etcd secrets
            if (!m_dev_mode) {
                // read CerFile value from config.json
                config_value_t* cert_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "certFile");
                if (cert_file_cvt == NULL) {
                    const char* err = "\"certFile\" key is missing";
                    LOG_WARN("%s", err);
                    throw(err);
                } else {
                    m_cert_file = cert_file_cvt->body.string;
                }

                // read keyFile value from config.json
                config_value_t* key_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "keyFile");
                if (key_file_cvt == NULL) {
                    const char* err = "\"keyFile\" key is missing";
                    LOG_WARN("%s", err);
                    throw(err);
                } else {
                    m_key_file = key_file_cvt->body.string;
                }

                // read Trust File value from config.json
                config_value_t* trust_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "trustFile");
                if (trust_file_cvt == NULL) {
                    const char* err = "\"trustFile\" key is missing";
                    LOG_WARN("%s", err);
                    throw(err);
                } else {
                    m_trust_file = trust_file_cvt->body.string;
                }

            } else {
                 m_cert_file ="";
                 m_key_file = "";
                 m_trust_file = "";
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
                m_config_mgr = NULL;
                m_env_config_client = NULL;

                // parse config file
                read_config(config_file_path);

                // get config mgr
                get_config_mgr();

                m_duration = SLEEP_DURATION_SECONDS;
                // Set log level
                set_log_level((log_lvl_t)m_log_level);

                // get env config client
                m_env_config_client = env_config_new();

                // Set env variables for env_config API
                const char* dev_mode = (m_dev_mode == true) ? "true" : "false";
                setenv("RequestEP", m_request_ep, 1);
                setenv("DEV_MODE", dev_mode, 1);

                setenv(m_client_cfg.c_str(), m_request_ep_cfg, 1);
                setenv("AppName", m_app_name, 1);
                char* request_ep[] = {m_request_ep};

                // Since VI is the server & sw_trigger_utility is the client, it is impersonating as VideoAnalytics to
                // get access to the allowed_clients list in VI.
                config_t* config = m_env_config_client->get_messagebus_config(m_config_mgr, request_ep, 1, CLIENT);

                m_msgbus_ctx = msgbus_initialize(config);
                if (m_msgbus_ctx == NULL) {
                    const char* err = "Failed to initialize message bus";
                    LOG_ERROR("%s", err);
                    throw err;
                }

                msgbus_ret_t ret = msgbus_service_get(
                m_msgbus_ctx, m_request_ep, NULL, &m_service_ctx);
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
                        LOG_INFO_0("Success putting poalod into env");
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
                        LOG_INFO_0("Success putting paylod into env");
                        LOG_INFO_0("Sending STOP_INGESTION sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if (ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- STOP_INGESTION";
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

        void get_config_mgr() {
            m_config_mgr = config_mgr_new("etcd",
                                        m_cert_file,
                                        m_key_file,
                                        m_trust_file);
        }
};


int main(int argc, char **argv) {
    try {
        SwTriggerUtility* sw_trigger_obj = NULL;
        if (argc > 3 ) {
            usage(argv[0]);
            return -1;
        }

        if (argc < 3) {
            argv[2] = CONFIG_FILE_PATH;
            if(argc == 2){
                // checking if 2nd argument is config json file, if yes then pass that as the configuration file path
                if((std::string(argv[1]).find("json", 0)) != std::string::npos) {
                    argv[2] = argv[1];
                } 
            } 
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
