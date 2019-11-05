# `HttpTestServer`

HttpTestServer runs a simple HTTP Test server with security being optional.

* To Run test rest data export test application

    1. To run the HttpTestServer
    ```
    $ cd [repo]/tools/HttpTestServer
    $ go run TestServer.go --dev_mode <Dev/Prod mode> --host <address of server> --port <port of server>
    ```

> **NOTE**: The certs provided to run the server are only samples and should never be re-used in production.
