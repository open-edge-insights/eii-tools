# Contents

- [Contents](#contents)
  - [Develop Python User Defined Functions using Jupyter Notebook](#develop-python-user-defined-functions-using-jupyter-notebook)
  - [Prerequisites for using Jupyter Notebooks](#prerequisites-for-using-jupyter-notebooks)
  - [Run Jupyter Notebook from web browsers](#run-jupyter-notebook-from-web-browsers)
  - [Run Jupyter Notebook using Visual Studio Code](#run-jupyter-notebook-using-visual-studio-code)

## Develop Python User Defined Functions using Jupyter Notebook

Jupyter Notebook is an open-source web application that allows you to create and share documents that contain live code, equations, visualizations, and narrative text. Jupyter Notebook supports the latest versions of the browsers such as Chrome, Firefox, Safari, Opera, and Edge. Some of the uses of Jupyter Notebook include:

- Data cleaning and transformation
- Numerical simulation
- Statistical modeling
- Data visualization
- Machine learning, and so on.

The web-based IDE of Jupyter Notebook allows you to develop User Defined Functions (UDFs) in Python. This tool provides an interface for you to interact with the Jupyter Notebook to write, edit, experiment, and create python UDFs. It works along with the [jupyter_connector](https://github.com/open-edge-insights/video-common/tree/master/udfs/python/jupyter_connector.py) UDF for enabling the IDE for UDF development. You can use a web browser or Visual Studio Code (VS Code) to use Jupyter Notebook for UDF development.

For more information on how to write and modify an OpenCV UDF, refer to the [opencv_udf_template.ipynb](opencv_udf_template.ipynb) (sample OpenCV UDF template). This sample UDF uses the OpenCV APIs to write a sample text on the frames, which can be visualized in the **Visualizer** display. While using this UDF, ensure that the encoding is disabled. Enabling the encoding will automatically remove the text that is added to the frames.

> **Note:**
> Custom UDFs like the `GVASafetyGearIngestion` are specific to certain use cases only. Do not use Jupyter Notebook with these custom UDFs. Instead, modify the `VideoIngestion` pipeline to use the `GVA ingestor` pipeline and modify the config to use the `jupyter_connector UDF`.
> In this document, you will find labels of 'Edge Insights for Industrial (EII)' for filenames, paths, code snippets, and so on. Consider the references of EII as Open Edge Insights (OEI). This is due to the product name change of EII as OEI.

## Prerequisites for using Jupyter Notebooks

The following are the prerequisites for using Jupyter Notebook to develop UDFs:

- Jupyter Notebook requires a set of configs, interfaces, and the public and private keys to be present in [etcd](https://etcd.io/). To meet this prerequisite, ensure that an entry for Jupyter Notebook with its relative path from the `[IEdgeInsights](../../)` directory is set in any of the `.yml` files present in the [build/usecases](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases) directory.
  - Refer the following example to add the entry in the [video-streaming.yml](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases/video-streaming.yml) file.

    ```yml
        AppContexts:
        ---snip---
        - tools/JupyterNotebook
    ```

- Ensure that in the config of either `VideoIngestion` or `VideoAnalytics` the [jupyter_connector](https://github.com/open-edge-insights/video-common/tree/master/udfs/python/jupyter_connector.py) UDF is enabled to connect to Jupyter Notebook. Refer the following example to connect `VideoIngestion` to `JupyterNotebook`. Change the config in the [config.json](https://github.com/open-edge-insights/video-ingestion/blob/master/config.json):

    ```javascript
        {
            "config": {
                "encoding": {
                    "type": "jpeg",
                    "level": 95
                },
                "ingestor": {
                    "type": "opencv",
                    "pipeline": "./test_videos/pcb_d2000.avi",
                    "loop_video": true,
                    "queue_size": 10,
                    "poll_interval": 0.2
                },
                "sw_trigger": {
                    "init_state": "running"
                },
                "max_workers":4,
                "udfs": [{
                    "name": "jupyter_connector",
                    "type": "python",
                    "param1": 1,
                    "param2": 2.0,
                    "param3": "str"
                }]
            }
        }
    ```

## Run Jupyter Notebook from web browsers

Perform the following steps to develop UDF using the Jupyter Notebook from a web browser:

1. In the terminal, run the following command:

    ```sh
        python3 builder.py -f usecases/video-streaming.yml
    ```

2. Refer the [IEdgeInsights/README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md) to provision, build and run the tool along with the OEI recipe or stack.

3. To see the logs, run the following command:

    ```sh
        docker logs -f ia_jupyter_notebook
    ```

4. In the browser, from the logs, copy and paste the URL along with the token. Refer to the following sample URL:

    ```sh
        http://127.0.0.1:8888/?token=5839f4d1425ecf4f4d0dd5971d1d61b7019ff2700804b973
    ```
  
    >**Note:**
    >
    > If you are accessing the server remotely, replace the IP address '127.0.0.1' with the host IP.

5. After launching the `Jupyter Notebook` service in a browser, from the list of available files, run the [main.ipynb](main.ipynb) file. Ensure that the `Python3.8` kernel is selected.

6. If required, to experiment and test the UDF, you can modify and rerun the process method of the [udf_template.ipynb](udf_template.ipynb) file.

7. To send parameters to the custom UDF, add them in the `jupyter_connector` UDF config provided to either `VideoIngestion` or `VideoAnalytics`. You can access the parameters in the [udf_template.ipynb](udf_template.ipynb) constructor in the `udf_config` parameter.

    >**Note:**
    >
    > The `udf_config` parameter is a dictionary (dict) that contains all these parameters. For more information, refer to the sample UDF from the [pcb_filter.py](https://github.com/open-edge-insights/video-common/blob/master/udfs/python/pcb/pcb_filter.py) file.
    > After modifying or creating a new UDF, run `main.ipynb` and then, restart **VideoIngestion** or **VideoAnalytics** with which you have enabled the `Jupyter Notebook` service.

8. To save or export the UDF, click **Download as** and then, select **(.py)**.

  > **Note:**
  >
  > To use the downloaded UDF, place it in the [../../common/video/udfs/python](https://github.com/open-edge-insights/video-common/blob/master/udfs/python) directory or integrate it with the `Custom UDFs`.

## Run Jupyter Notebook using Visual Studio Code

Perform the following steps to use Visual Studio Code (VS Code) to develop a UDF:

1. In the terminal, run the following command:

    ```sh
        python3 builder.py -f usecases/video-streaming.yml
    ```

2. Refer the [IEdgeInsights/README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md) to provision, build and run the tool along with the OEI recipe or stack.

3. To see the logs, run the following command:

    ```sh
        docker logs -f ia_jupyter_notebook
    ```

4. In the consolidated `build/docker-compose.yml` file, for the `ia_jupyter_notebook` service, change `read_only: true` to `read_only: false`.
5. Run the `docker-compose up -d ia_jupyter_notebook` command.
6. In VS Code, install the `Remote - Containers` extension.
7. Using the shortcut key combination `(Ctrl+Shift+P)` access the Command Palette.
8. In the Command Palette, run the `Remote-Containers: Attach to Running Container` command.
9. Select the `ia_jupyter_notebook` container.
10. In the `ia_jupyter_notebook` container, install the `Python` and `Jupyter` extensions.
11. In the Command Palette, run the `Jupyter: Specify local or remote Jupyter server for connections` command.
12. Choose `Existing: Specify the URI of an existing server` when prompted to select how to connect to Jupyter Notebook.
13. Enter the server's URI (hostname) with the authentication token (included with a ?token= URL parameter), when prompted to enter the URI of a Jupyter server. Refer to the sample URL mentioned in the previous procedure.
14. Open the `/home/eiiuser` folder to update the respective udf_template and the main notebooks and re-run.
15. To save the UDF, go to **More Actions (...)**, and then, select **Export**.
16. When prompted **Export As**, select **Python Script**.
17. From the **File** menu, click **Save As**.
18. Select **Show Local**.
19. Enter the name and save the file.

> **Note:**
>
> You cannot upload files to the workspace in VS Code due to the limitation with the Jupyter Notebook plugin. To use this functionality, access the Jupyter notebook through a web browser.
