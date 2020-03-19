# EIS FPS calculator

This module calculates the FPS of any EIS modules based on the stream published by that respective module.

## Installing FPS calculator requirements

1. To install the requirements to start FPS Calculator run the below commands.

    ```sh
        source ./env.sh
        sudo -E ./install.sh
    ```

## Running FPS calculator

1. Set environment variables accordingly in [config.json](config.json)

2. Set the required output stream/streams and appropriate stream config in [config.json](config.json) file.

3. If using FpsCalculator in IPC mode, make sure to set required permissions to socket file created in `EIS_INSTALL_PATH`

    ```sh
        sudo chmod -R 777 /opt/intel/eis/sockets
    ```
    Note: This step is required everytime publisher is restarted in IPC mode.
    Caution: This step will make the streams insecure. Please do not do it on a production machine.

4. If using FpsCalculator in PROD mode, make sure to set required permissions to certificates.

    ```sh
        sudo chmod -R 755 ../../docker_setup/provision/Certificates/ca
        sudo chmod -R 755 ../../docker_setup/provision/Certificates/root
    ```
    Note : This step is required everytime provisioning is done. 
    Caution: This step will make the certs insecure. Please do not do it on a production machine.

5. Run the below command to start the FPS Calculator.

    ```sh
        python3.6 fps_calculator.py
    ```
