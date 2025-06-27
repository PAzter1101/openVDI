# OpenVDI Repository Overview

## Purpose
OpenVDI is an open-source Python application that orchestrates Virtual Desktop Infrastructure (VDI) and provides end-user access through a Guacamole interface. The system automatically scales VDI instances based on configurable parameters and maintains "buffers" of ready-to-use virtual machines in different states to ensure quick user access.

## General Setup
The application uses a microservices architecture deployed via Docker Compose with the following components:

### Core Services
- **OpenVDI Server**: Main orchestration service that manages VDI lifecycle and scaling
- **Worker**: Redis-based message processing service for background tasks
- **Guacamole**: Web-based remote desktop gateway providing the user interface
- **Guacd**: Guacamole daemon for handling remote desktop protocols
- **PostgreSQL**: Database backend for Guacamole configuration and user data
- **Redis**: Message broker for inter-service communication

### Installation Process
1. Clone repository and run `init.sh` to prepare folders and initialize Guacamole database
2. Configure environment variables in `server/.env` (copy from `.env-example`)
3. Deploy with `docker compose up -d`
4. Access via browser at `http://localhost:8080` with default credentials `guacadmin/guacadmin`

## Repository Structure

```
openVDI/
├── .github/workflows/          # CI/CD workflows
│   └── docker-image.yaml      # Docker build automation
├── server/                     # Main OpenVDI orchestration service
│   ├── providers/              # VDI provider implementations
│   │   ├── provider.py         # Abstract provider interface
│   │   └── pve.py             # Proxmox VE provider implementation
│   ├── config.py              # Configuration management with Pydantic
│   ├── guaca.py               # Guacamole API integration
│   ├── main.py                # Application entry point
│   ├── open_vdi.py            # Core VDI orchestration logic
│   ├── worker.py              # Worker task management
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Server container definition
│   └── .env-example           # Configuration template
├── worker/                     # Background task processor
│   ├── main.py                # FastStream Redis worker
│   ├── requirements.txt       # Worker dependencies
│   └── Dockerfile             # Worker container definition
├── docker-compose.yaml        # Multi-service deployment configuration
├── init.sh                    # Setup script for initial deployment
└── README.MD                  # Project documentation
```

## Key Features

### VDI Lifecycle Management
The system manages VDI instances through four states:
1. **Non-existent**: VDI not yet created
2. **Stopped**: VDI created but powered off
3. **Running**: VDI powered on and ready for connection
4. **User Connected**: VDI actively in use

### Buffer System
- **BUFFER_RV**: Maintains running VDIs ready for immediate user connection
- **BUFFER_SV**: Maintains stopped VDIs ready for quick startup when needed
- **MIN_VDI/MAX_VDI**: Defines the minimum and maximum total VDI count
- **MIN_RUNNED_VDI**: Ensures minimum number of running VDIs at all times

### Provider Architecture
Extensible provider system currently supporting:
- **Proxmox VE (PVE)**: Primary hypervisor integration
- Abstract provider interface allows for additional hypervisor support

## CI/CD Configuration

### GitHub Workflows
- **Docker Image CI** (`.github/workflows/docker-image.yaml`):
  - Triggers on push/PR to default branch
  - Builds both server and worker Docker images
  - Uses timestamped tags for image versioning
  - Runs on Ubuntu latest with checkout@v4

### Technology Stack
- **Backend**: Python 3.10 with async/await (Trio framework)
- **Message Queue**: Redis with FastStream
- **Database**: PostgreSQL 16.9
- **Remote Access**: Apache Guacamole
- **Containerization**: Docker & Docker Compose
- **Configuration**: Pydantic Settings with environment variables
- **Hypervisor Integration**: Proxmoxer for Proxmox VE API

### Key Dependencies
- **Server**: `trio`, `proxmoxer`, `guacapy`, `pydantic-settings`, `redis`, `faststream`
- **Worker**: `faststream`, `redis`, `pydantic`

The system is designed for high availability and automatic scaling, making it suitable for organizations needing on-demand virtual desktop access with minimal user wait times.