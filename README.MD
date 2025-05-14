# OpenVDI
OpenVDI is an open source Python application that orchestrates VDI and provides end-user access through a guacamole interface.

OpenVDI automatically scales the number of VDIs in different "states".

You set the desired value for the min/max count and the value for "buffers" (more about buffers can be found in the "buffers" section), and OpenVDI will support machines according to these parameters.

## Installation
1. Run:
    ```sh
    git clone https://github.com/PAzter1101/openVDI.git
    cd openVDI
    chmod 700 ./init.sh
    ./init.sh
    cp server/.env.example server/.env
    ```

2. Specify the necessary settings in `.env`
3. Run:
    ```sh
    docker compose up -d
    ```

## Usage
1. Open a browser and go to `http://localhost:8080`
2. Login with the default credentials guacadmin/guacadmin
3. You can now use guacamole as usual.

## Buffers
todo: add description of how it works
