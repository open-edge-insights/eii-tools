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


#define SERVICE_NAME "sw_trigger_utility"
#define CONFIG_FILE_PATH "../config/config.json"

#define SLEEP_DURATION_SECONDS 120
#define START_INGESTION_STR "START_INGESTION"
#define STOP_INGESTION_STR "STOP_INGESTION"
#define REQUEST_HONORED "REQUEST_HONORED"
#define REQUEST_NOT_HONORED "REQUEST_NOT_HONORED"
#define REQUEST_ALREADY_RUNNING "REQUEST_ALREADY_RUNNING"
#define REQUEST_ALREADY_STOPPED "REQUEST_ALREADY_STOPPED"
#define SUB "sub"

#define FREE_MEMORY(msg_env) { \
    if(msg_env != NULL) { \
        msgbus_msg_envelope_destroy(msg_env); \
        msg_env = NULL; \
    } \
}

enum SwTrigger {
        START_INGESTION,
        STOP_INGESTION
    };

void usage(const char* name) {
        std::cout <<name<<" usage: ./sw_trigger_vi [Duration to ingest in seconds] [<START_INGESTION | STOP_INGESTION>] \n \
                    -> Optional argument: START_INGESTION | STOP_INGESTION - Action to send to Video Ingestion service  \n \
                    -> Optional argument: Duration to ingest in seconds (default=120 seconds). \
                    NOTE: As a prerequisite update the config.json file for sw_trigger_utility based on the config need.  \
                    Refer READMe.md for more details on each options" << std::endl;

        std::cout <<" Examples: 1. sw_trigger_utility \n \
                                2. sw_trigger_utility 300 \
                                3. sw_trigger_utility START_INGESTION \
                                4. sw_trigger_utility STOP_INGESTION " \
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
        int m_log_level;
        size_t m_num_of_cycles;
        char* m_server_client;
        char* m_sw_trigger_utility_cfg;
        bool m_dev_mode;
        char* m_app_name;
        char* m_cert_file;
        char* m_key_file;
        char* m_trust_file;
        char* m_client;

    public:
        void read_config() {
            // parse config file
            config_t* config_file_cfg = json_config_new(CONFIG_FILE_PATH);
            if ( config_file_cfg == NULL ) {
                const char* err = "Failed to load JSON configuration of sw trigger utility";
                LOG_ERROR("%s", err);
                throw err;
            }

            // log_level
            config_value_t* log_level_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "log_level");
            if ( log_level_cvt == NULL ) {
                const char* err = "\"log_level\" key is missing, setting to default log level as debug";
                LOG_WARN("%s", err);
                m_log_level = 3; // Since, we are not exiting, setting default to continue
            } else {
                m_log_level = log_level_cvt->body.integer;
            }

            //num_of_cycles

            config_value_t* num_of_cyles_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "num_of_cyles");
            if ( num_of_cyles_cvt == NULL ) {
                const char* err = "\"num_of_cyles\" key is missing, setting to default (2 cycles)";
                LOG_WARN("%s", err);
                m_num_of_cycles = 2;
            } else {
                m_num_of_cycles = num_of_cyles_cvt->body.integer;
            }


            config_value_t* server_client_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "server_client");
            if ( server_client_cvt == NULL ) {
                const char* err = "\"server_client\" key is missing, setting to default";
                LOG_WARN("%s", err);
                m_server_client = "VideoIngestion/sw_trigger_utility";
            } else {
                m_server_client = server_client_cvt->body.string;
            }

            config_value_t* sw_trigger_utility_cfg_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "sw_trigger_utility_cfg");
            if ( sw_trigger_utility_cfg_cvt == NULL ) {
                const char* err = "\"sw_trigger_utility_cfg\" key is missing, resetting to default connection IP as localhost & default port";
                LOG_WARN("%s", err);
                m_sw_trigger_utility_cfg = "zmq_tcp,127.0.0.1:66013";
            } else {
                m_sw_trigger_utility_cfg = sw_trigger_utility_cfg_cvt->body.string;
            }

            config_value_t* dev_mode_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "dev_mode");
            if ( dev_mode_cvt == NULL ) {
                const char* err = "\"dev_mode\" key is missing, resetting to default dev mode";
                LOG_WARN("%s", err);
                m_dev_mode = true;

            } else {
                m_dev_mode = dev_mode_cvt->body.boolean;
            }

            config_value_t* app_name_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "app_name");
            if ( app_name_cvt == NULL ) {
                const char* err = "\"app_name\" key is missing, setting to default";
                LOG_WARN("%s", err);
                m_app_name = "VideoAnalytics";
            } else {
                m_app_name = app_name_cvt->body.string;
            }

            // Only if prod mode then read etcd secrets
            if(!m_dev_mode) {
                // read CerFile value from config.json
                config_value_t* cert_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "certFile");
                if ( cert_file_cvt == NULL ) {
                    const char* err = "\"certFile\" key is missing";
                    LOG_WARN("%s", err);
                    throw(err);
                } else {
                    m_cert_file = cert_file_cvt->body.string;
                }

                // read keyFile value from config.json
                config_value_t* key_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "keyFile");
                if ( key_file_cvt == NULL ) {
                    const char* err = "\"keyFile\" key is missing";
                    LOG_WARN("%s", err);
                    throw(err);
                } else {
                    m_key_file = key_file_cvt->body.string;
                }
                
                // read Trust File value from config.json
                config_value_t* trust_file_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "trustFile");
                if ( trust_file_cvt == NULL ) {
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

            config_value_t* client_cvt = config_file_cfg->get_config_value(config_file_cfg->cfg,
                                                              "client");
            if ( client_cvt == NULL ) {
                const char* err = "\"client\" key is missing";
                LOG_WARN("%s", err);
            } else {
                m_client = client_cvt->body.string;
            }
        }

        /**
        * Constructor
        * Constructor of SwTriggerUtility class        
        */

        SwTriggerUtility() {
            try {
                // Initialize default values
                m_msgbus_ctx = NULL;
                m_service_ctx = NULL;
                m_config_mgr = NULL;
                m_env_config_client = NULL;

                // parse config file
                read_config();

                // get config mgr
                get_config_mgr();

                m_duration = SLEEP_DURATION_SECONDS;
                // Set log level
                set_log_level((log_lvl_t)m_log_level);

                // get env config client
                m_env_config_client = env_config_new();

                // Set env variables for env_config API
                const char* dev_mode = (m_dev_mode == true) ? "true" : "false";
                setenv("DEV_MODE", dev_mode, 1);
                std::string client_cfg = std::string(m_client) + "_cfg";
                setenv(client_cfg.c_str(), m_sw_trigger_utility_cfg, 1);
                setenv("AppName", m_app_name, 1);
                char* server_client[] = {m_server_client};

                // Since VI is the server & sw_trigger_utility is the client, it is impersonating as VideoAnalytics to 
                // get access to the allowed_clients list in VI.  
                config_t* config = m_env_config_client->get_messagebus_config(m_config_mgr, server_client, 1, SUB);

                m_msgbus_ctx = msgbus_initialize(config);
                if ( m_msgbus_ctx == NULL ) {
                    const char* err = "Failed to initialize message bus";
                    LOG_ERROR("%s", err);
                    throw err;
                }

                msgbus_ret_t ret = msgbus_service_get(
                m_msgbus_ctx, SERVICE_NAME, NULL, &m_service_ctx);
                if ( ret != MSG_SUCCESS ) {
                    const char* err = "Failed to initialize service, msgbus_service_get failed";
                    LOG_ERROR("%s", err);
                    throw err;
                }
            }
            catch( std::exception& ex ) {
                LOG_ERROR("Exception = %s occurred in construction of SW_trigger_utility object ",ex.what());
            }
        }

        ~SwTriggerUtility() {
            if(m_service_ctx != NULL)
                msgbus_recv_ctx_destroy(m_msgbus_ctx, m_service_ctx);
            if(m_msgbus_ctx != NULL)
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
                if(ret != MSG_SUCCESS) {
                    // Interrupt is an acceptable error
                    const char* err = "";
                    if(ret != MSG_ERR_EINTR)
                        err = "Interrupt received. Failed to receive SW trigger ACK";
                    else
                    err = "Failed to receive SW trigger ACK";
                    throw err;
                    LOG_ERROR("%s",err);

                }

                msg_envelope_elem_body_t* ack_env;
                ret = msgbus_msg_envelope_get(msg, "ack_for_sw_trigger", &ack_env);
                if(ret != MSG_SUCCESS) {
                    const char* err = "Failed to receive ACK from server for the sw_trigger";
                    LOG_ERROR("%s",err);
                    throw(err);
                }

                if(MSG_ENV_DT_STRING != ack_env->type) {
                    const char* err = "ACK received from server for the sw_trigge has a wrong data type";
                    LOG_ERROR("%s",err);
                    throw(err);
                }

                if(!strcmp(REQUEST_HONORED, ack_env->body.string)) {
                    LOG_INFO_0("REQUEST HONORED ");
                } else if(!strcmp(REQUEST_NOT_HONORED, ack_env->body.string)) {
                    LOG_INFO_0("REQUEST NOT HONORED ");
                } else if(!strcmp(REQUEST_ALREADY_RUNNING, ack_env->body.string)) {
                    LOG_INFO_0("DUPLICATE REQUEST SENT BY CLIENT, AS INGESTION IS ALREADY RUNNING");
                } else if(!strcmp(REQUEST_ALREADY_STOPPED, ack_env->body.string)) {
                    LOG_INFO_0("DUPLICATE REQUEST SENT BY CLIENT AS INGESTION IS ALREADY STOPPED");
                }
                else {
                    LOG_ERROR_0("Received improper ack message. Exiting..");
                }
                FREE_MEMORY(msg);
            } catch(std::exception& ex) {
                LOG_ERROR("Exeption : %s occured during receving ACK from VI ", ex.what());
                FREE_MEMORY(msg);
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
                switch(trig) {
                    case START_INGESTION: {
                        LOG_INFO_0("Sending START_INGESTION SW trigger..");
                        msg_envelope_elem_body_t* sw_trigger = msgbus_msg_envelope_new_string(START_INGESTION_STR);
                        msg = msgbus_msg_envelope_new(CT_JSON);
                        msgbus_msg_envelope_put(msg, "sw_trigger", sw_trigger);
                        LOG_INFO_0("Sending START_INGESTION sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if(ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- START_INGESTION";
                            LOG_ERROR("%s",err);
                            throw err;
                        }
                        
                    }
                    break;
                    case STOP_INGESTION: {
                        LOG_INFO_0("Sending STOP_INGESTION SW trigger..");
                        msg_envelope_elem_body_t* sw_trigger = msgbus_msg_envelope_new_string(STOP_INGESTION_STR);
                        msg = msgbus_msg_envelope_new(CT_JSON);
                        msgbus_msg_envelope_put(msg, "sw_trigger", sw_trigger);
                        LOG_INFO_0("Sending STOP_INGESTION sw trigger");
                        ret = msgbus_request(m_msgbus_ctx, m_service_ctx, msg);
                        if(ret != MSG_SUCCESS) {
                            const char* err = "FAILED TO SEND SW TRIGGER -- STOP_INGESTION";
                            LOG_ERROR("%s",err);
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
                LOG_ERROR("Exception: %s occured while sending software trigger ",ex.what());
                FREE_MEMORY(msg);
            }
        }

        // set functionget_config
        void set_duration(int dur) {
            m_duration = dur;
        }

        /**
        * Function to perform the cycle of "START_INGESTION"->"Allow ingestion to happen for someime" -> "STOP_INGESTION"
        *  
        * */
        void perform_full_cycle() {
            size_t count = m_num_of_cycles;
            while ( count >= 0 ) {
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
        if(argc > 2) {
            usage(argv[0]);
            return -1;
        }
        sw_trigger_obj = new SwTriggerUtility();

        switch(argc) {
            case 1: {
                sw_trigger_obj->perform_full_cycle();
            }
            break;
            case 2: {
                if(!strcmp(argv[1],"START_INGESTION")) {
                    sw_trigger_obj->send_sw_trigger(START_INGESTION);
                    sw_trigger_obj->recv_ack();
                } else if(!strcmp(argv[1],"STOP_INGESTION")) {
                    sw_trigger_obj->send_sw_trigger(STOP_INGESTION);
                    sw_trigger_obj->recv_ack();
                } else if(is_number(std::string(argv[1]))) {
                    sw_trigger_obj->set_duration(std::stoi(std::string(argv[1])));
                    sw_trigger_obj->perform_full_cycle();
                } else {
                    LOG_ERROR_0("ERROR: Provide proper commandline args");
                    usage(argv[0]);
                }
            }
            break;
            default: {
                    LOG_ERROR_0("ERROR: Provide proper commandline args");
                    usage(argv[0]);
            }
        };
    } catch(std::exception &ex) {
        LOG_ERROR("exception in main of sw-trigger--utility: %s",ex.what());
    }
    return 0;
}
