SHELL := /bin/bash
CWD = $(shell pwd)
IEI_INSTALL_DIR = /opt/intel/iei
DIST_LIBS_DIR = $(IEI_INSTALL_DIR)/dist_libs
PYTHON_PATH = $(DIST_LIBS_DIR)/ImageStore/protobuff/py:$(DIST_LIBS_DIR)/DataBusAbstraction/py:$(DIST_LIBS_DIR)/DataBusAbstraction/:$(DIST_LIBS_DIR)/ImageStore/test/py/:$(DIST_LIBS_DIR)
TARGET_CERT_PATH = /etc/ssl
CERT_PATH = /tmp
IMAGE_DIR = $(IEI_INSTALL_DIR)/saved_images
DISPLAY_IMG=true
HOST=localhost
VISUALIZER_VERSION = 1.5

# Pls add/remove any switch as per the needs
# secure args
SECURE_VISUALIZE_ARGS = -c $(TARGET_CERT_PATH) --host $(HOST) -d $(DISPLAY_IMG) -D false -i $(IMAGE_DIR) -P false
# unsecure args
NON_SECURE_VISUALIZE_ARGS = --host $(HOST) -d $(DISPLAY_IMG) -D true -i $(IMAGE_DIR) -P false

build:
	./build_visualizer_docker_image.sh "$(VISUALIZER_VERSION)"

run:
	docker run --rm --name ia_visualizer -it \
			   -v $(DIST_LIBS_DIR):$(DIST_LIBS_DIR) \
			   -v $(IMAGE_DIR):$(IMAGE_DIR) \
			   -v $(CERT_PATH):$(TARGET_CERT_PATH) \
			   -v $(CWD)/config.json:/iei/config.json \
			   -v /tmp/.X11-unix:/tmp/.X11-unix \
			   -e no_proxy=$no_proxy,$(HOST) \
			   -e DIST_LIBS_DIR=$(DIST_LIBS_DIR) \
			   -e PYTHONPATH=$(PYTHON_PATH) \
			   -u ieiuser \
			   --net=host \
			   --ipc=host \
			   --log-driver json-file \
			   --log-opt max-size=10m \
			   --log-opt max-file=5 \
			   --env="DISPLAY" \
			   -it ia/visualizer:$(VISUALIZER_VERSION)\
			   $(SECURE_VISUALIZE_ARGS)
