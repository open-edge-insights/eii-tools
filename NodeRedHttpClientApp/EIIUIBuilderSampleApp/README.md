# SampleWebAPP using UIBuilder Node Module

This is SampleWebApp which built based on UIBuilder NodeRed community module which fetches the data from EII RestDataExport and display as an WebApplication

## Installing UI Builder Node

Goto `Palette Manager` and install UI Builder

![img_pallet.png](./images/img_pallet.png)

> **Note**
> For More details on Pallete Manager: https://nodered.org/docs/user-guide/editor/palette/manager


## Import EIISampleAPP Flows

*   Import the Workflow [flows.json](./flows.json) file to NodeRed dashboard using `menu` icon in top right corner as follows
    
      ![images/imageimportnodes.png](./images/imageimportnodes.png)

*   Click `Import` Button

*   Update `url` in all nodes wherever applicable and use `https` if you are running RDE in ProdMode.

## Editing Files of UI Builder

1. `Double Click` on UI Builder Node and Edit following files and copy the content of the below files into UI builder nodered files in Edit Files section.
    
    1. [index.html](./index.html)
    2. [index.css](./index.css)
    3. [index.js](./index.js)

![img_edit_files.png](./images/img_edit_files.png)

2. Save the files

**Note** Make sure flow is deployed.

## Accesing UI Builder

1.  Access UI Builder App from following `Endpoint`

    http://<url:port>/uibuilder/









