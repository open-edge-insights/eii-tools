# `HttpTestServer`

HttpTestServer runs a simple HTTP Test server with security being optional.

* Generate the Certificate required to run the Http Test Server using the following command

  ```
  $ ./generate_testserver_cert.sh test-server-ip
  ```

* To Run test rest data export test application without CSL setup

    1. To run the HttpTestServer
    ```
    $ cd IEdgeInsights/tools/HttpTestServer
    $ go run TestServer.go --dev_mode <true/false> --host <address of server> --port <port of server>
    ```
* To Run test rest data export test application with the CSL setup

    1. To run the HttpTestServer
    ```
    $ cd IEdgeInsights/tools/HttpTestServer
    $ go run TestServer.go --dev_mode false --host <address of test server> --port <port of test server> --rdehost <address of Rest Data Export server> --rdeport <port of Rest Data Export server>
    ```

    2. Copy the ca certificate generated in the certificates folder to the /opt/intel/eis folder
    ```
    $ sudo cp certificates/ca_cert.pem /opt/intel/eis/cert.pem
    ```

    ***NOTE***: server_cert.pem is valid for 365 days from the day of generation

> **NOTE**: The certs provided to run the server are only samples and should never be re-used in production.
