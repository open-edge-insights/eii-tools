# NodeRedHttpClientApp

This Node-RED in-built http node based client App acts as client for the OEI RestDataExport and brings the OEI Classifier data to Node-RED ecosystem.

## Setting Up NodeRed

  Node-RED provides various options to install and set up Node-RED in your environment. For more information on installation and setup, refer to the [Node-RED documenation](https://nodered.org/docs/getting-started/local).

   >**Note:** For quick setup, install using `docker`
   >
   > ```sh
   >    docker run -it -p 1880:1880 --name myNodeRed nodered/node-red
   > ```

## Getting OEI UDF Classifier results data to Node-RED Environment Using Node-RED HTTPClient

> **Note**: RestDataExport should be running already as a prerequisite.  
> Refer to the RestDataExport [Readme](https://github.com/open-edge-insights/eii-rest-data-export)

1. Drag the `http request` node of Node-RED's default nodes to your existing workflow.

   ![images/imagehttprequestnode.png](./images/imagehttprequestnode.png)

2. Update the `properties` of node as follows:

   For `DEV mode`:
    - Refer to the dialog properties for setting up the `DEV` mode in the Node-Red dashboard

      ![images/imagedevmode.png](./images/imagedevmode.png)

   For `PROD Mode`:
   - Refer to the dialog properties for setting up the `PROD` mode in the Node-RED dashboard

      ![imageprodmode.png](./images/imageprodmode.png)

   For Prod Mode TLS `ca_cert.pem` import.
   **Note:** This `ca_cert.pem` will be part of the OEI certificate bundle. Refer the `[WORKDIR]/IEdgeInsights/build/Certificates/` directory.

   ![imageprodmodetlscert.png](./images/imageprodmodetlscert.png)

   > **Note:**
   >
   >    1. For the `DEV` mode, do not enable or attach the certificates.
   >    2. Update the `IP` address as per the `RestDataExport` module running machine IP.
   >    3. For more details on Node-RED's `http request` module, refer to [Http requset](https://stevesnoderedguide.com/node-red-http-request-node-beginners).

## Sample Workflow

The attached workflow document is sample workflow by updating the `RestDataExport` IP Address in the `http request` module,

1. Import the Sample Workflow [flows.json](./flows.json) file to NodeRed dashboard using `menu` icon in top right corner as follows

   ![images/imageimportnodes.png](./images/imageimportnodes.png)

2. Click `Import`

3. Update the `URL` of `http request` node with `RestDataExport` module running the machine IP Address

   >**Note:**
   >
   > - For detail, refer to [import export] (https://nodered.org/docs/user-guide/editor/workspace/import-export)
   > - The classifier results will be logged in the debug window.
