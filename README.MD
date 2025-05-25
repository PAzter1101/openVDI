# OpenVDI
OpenVDI is an open source Python application that orchestrates VDI and provides end-user access through a guacamole interface.

OpenVDI automatically scales the number of VDIs in different "states".

You set the desired value for the min/max count and the value for "buffers" (more about buffers can be found in the ["buffers" section](/README#buffers)), and OpenVDI will support machines according to these parameters.

## Installation
1. Run:
    ```sh
    git clone https://github.com/PAzter1101/openVDI.git
    cd openVDI
    chmod 700 ./init.sh
    ./init.sh
    cp server/.env-example server/.env
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

```

│ minVDI │
│        │
▼────────▼──────────┐
│  User connected   │
├───────────────────┴───────────────┐
│                        Running    │
├───────────────────▲───────────────▲───────────────┐
│                   │               │    Stopped    │
▲───────────────────┼───────────────┼───────────────▲───────▲
│                   │               │               │       │
│                   │               │               │       │
│                   │               │               │       │
│                   │   Buffer RV   │   Buffer SV   │       │
│                   └───────────────┴───────────────┘       │
│                           maxVDI                          │
└───────────────────────────────────────────────────────────┘
```

In order for the user to always be able to quickly connect, openVDI supports different states of the VDI life cycle:

1. Does not exist yet;
2. Stopped;
3. Running;
4. User connected.

The transition between these states takes a long time, so openVDI uses "buffers" to keep some amount of VDI in certain states "in reserve". Currently, there are 2 buffers:

**BUFFER_RV** - the number of VDIs that must be in the "running" status and ready for a user to connect to them (not have other working users).
If a user connects to such a VDI, then the number of "free" and "running" VDIs will decrease and openVDI will turn on more VDIs to return the correct number, specified in BUFFER_RV.
This also works in the opposite direction. If the user disconnects, openVDI will turn off extra VDIs to free up hypervisor resources.

**BUFFER_SV** - the number of VDIs that must be in the "stopped" status and ready to quickly turn on if openVDI needs additional VDIs.
When openVDI turns on VDI to balance BUFFER_RV and the current status, the number of disabled VDIs becomes smaller - and the process of creating new VDIs starts to return the correct number, specified in BUFFER_SV. This also works in the opposite direction - if openVDI has turned off a lot of VDIs and now their number is greater than BUFFER_SV - then openVDI will delete unnecessary VDIs (the oldest VDIs are the priority for deletion, in order to maintain rotation).
