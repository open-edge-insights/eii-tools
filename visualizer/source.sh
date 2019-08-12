#!/bin/bash

# Init the EIS env varilables
source ../../docker_setup/.env

export DIST_LIBS_DIR=$IEI_INSTALL_PATH/dist_libs
export DEV_MODE=$DEV_MODE
export PROFILING=$PROFILING

# Path to Image directory where the visualized images are saved
# Have this set if save_image option is true in etcd config
export IMAGE_DIR=$IEI_INSTALL_PATH/saved_images

# Init the subscription variables
export AppName=Visualizer
export SubTopics=VideoAnalytics/camera1_stream_results
export camera1_stream_results_cfg=zmq_tcp,127.0.0.1:65013
