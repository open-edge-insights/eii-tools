**Contents**

- [Jupyter Notebook usage to develop python UDFs](#jupyter-notebook-usage-to-develop-python-udfs)
  - [Jupyter Notebook pre-requisites](#jupyter-notebook-pre-requisites)
  - [Running Jupyter Notebook](#running-jupyter-notebook)

# Jupyter Notebook usage to develop python UDFs

UDF development in python can be done using the web based IDE of Jupyter Notebook.
Jupyter Notebook is an open-source web application that allows you to create and share documents that contain live code, equations, visualizations and narrative text. Uses include: data cleaning and transformation, numerical simulation, statistical modeling, data visualization, machine learning, and much more.

This tool acts as an interface between user and Jupyter Notebook service allowing the user to interact with Jupyter Notebook to write, edit, experiment and create python UDFs.

It works along with the [jupyter_connector](https://github.com/open-edge-insights/video-common/tree/master/udfs/python/jupyter_connector.py) UDF for enabling the IDE for udf development.

## Jupyter Notebook pre-requisites

1. Jupyter Notebook expects a set of config, interfaces & public private keys to be present in ETCD as a pre-requisite.
    - To achieve this, please ensure an entry for Jupyter Notebook with its relative path from [IEdgeInsights](../../) directory is set in any of the .yml files present in [build/usecases](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases) directory.
    - An example has been provided below to add the entry in [video-streaming.yml](https://github.com/open-edge-insights/eii-core/tree/master/build/usecases/video-streaming.yml)

    ```yml
        AppContexts:
        ---snip---
        - tools/JupyterNotebook
    ```

2. Ensure the [jupyter_connector](https://github.com/open-edge-insights/video-common/tree/master/udfs/python/jupyter_connector.py) UDF is enabled in the config of either **VideoIngestion** or **VideoAnalytics** to be connected to JupyterNotebook. An example has been provided here for connecting **VideoIngestion** to **JupyterNotebook**, the config to be changed being present at [config.json](https://github.com/open-edge-insights/video-ingestion/blob/master/config.json):

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

## Running Jupyter Notebook

1. With the above pre-requisite done, please run the below command:

    ```sh
        python3 builder.py -f usecases/video-streaming.yml
    ```

2. Refer [IEdgeInsights/README.md](https://github.com/open-edge-insights/eii-core/blob/master/README.md) to provision, build and run the tool along with the EII recipe/stack.

3. Run the following command to see the logs:

    ```sh
        docker logs -f ia_jupyter_notebook
    ```

4. Copy paste the URL (along with the token) from the above logs in a browser. Below is a sample URL

    ```sh
        http://127.0.0.1:8888/?token=5839f4d1425ecf4f4d0dd5971d1d61b7019ff2700804b973
    ```

   Replace the '127.0.0.1' IP address with host IP, if you are accessing the server remotely.

   **Note:**
    > To achieve the same behaviour in Visual Studio Code(VSCode) instead of web browser, follow below steps:
    >
    >1. In the consolidated `build/docker-compose.yml` file change the `read_only: true` to `read_only: false` for the service `ia_jupyter_notebook`.
    >2. Run command `docker-compose up -d ia_jupyter_notebook`.
    >3. Install `Remote - Containers` extension in VSCode.
    >4. Run `Remote-Containers: Attach to Running Container` command from the Command Palette `(Ctrl+Shift+P)` and select `ia_jupyter_notebook` container.
    >5. Install `Python` and `Jupyter` extensions in the `ia_jupyter_notebook` container in the VSCode.
    >6. Run `Jupyter: Specify local or remote Jupyter server for connections` command from the Command Palette `(Ctrl+Shift+P)`.
    >7. When prompted to pick how to connect to Jupyter, select `Existing: Specify the URI of an existing server`.
    >8. When prompted to Enter the URI of a Jupyter server, provide the server's URI (hostname) with the authentication token included with a ?token= URL parameter as shown in the above example.
    >9. As you are attached to `ia_jupyter_notebook` container as part of step 4, please open folder `(Ctrl+K+Ctrl+O)` `/home/eiiuser` to update the respective udf_template and main notebooks and re-run.

5. Once the Jupyter Notebook service is launched in the browser, run the [main.ipynb](main.ipynb) file visible in the list of files available. Make sure Python3.8 kernel is selected.

6. The process method of [udf_template.ipynb](udf_template.ipynb) file available in the list of files can be altered and re-run to experiment and test the UDF.

7. If any parameters are to be sent to the custom udf by the user, they can be added in the **jupyter_connector** UDF config provided to either **VideoIngestion** or **VideoAnalytics** and can be accessed in the [udf_template.ipynb](udf_template.ipynb) constructor in the **udf_config** parameter which is a dict containing all these parameters. A sample UDF for reference has been provided at [pcb_filter.py](https://github.com/open-edge-insights/video-common/blob/master/udfs/python/pcb/pcb_filter.py).

> **Note:** After altering/creating a new udf, run main.ipynb  and restart **VideoIngestion** or **VideoAnalytics** with which you have enabled jupyter notebook service.

8. Once the user is satisfied with the functionality of the UDF, the udf can be saved/exported by clicking on the **Download as** option and selecting **(.py)** option. The downloaded udf can then be directly used by placing it in the [../../common/video/udfs/python](https://github.com/open-edge-insights/video-common/blob/master/udfs/python) directory or can be integrated and used with **CustomUDFs**.

> **Note:**
>
> - JupyterNotebook is not to be used with **CustomUDFs** like **GVASafetyGearIngestion** since they are specific to certain usecases only. Instead, the VideoIngestion pipeline can be modified to use GVA ingestor pipeline and config can be modifed to use **jupyter_connector** UDF.
> - A sample opencv udf template is provided at [opencv_udf_template.ipynb](opencv_udf_template.ipynb) to serve as an example for how a user can write an OpenCV UDF and modify it however required. This sample UDF uses OpenCV APIs to write a sample text on the frames, which can be visualized in the **Visualizer** display. Please ensure **encoding is disabled** when using this UDF since encoding enabled automatically removes the text added onto the frames.
