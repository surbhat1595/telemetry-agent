# Percona Telemetry

[![CI](https://github.com/percona/telemetry-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/percona/telemetry-agent/actions/workflows/ci.yml)
[![CLA assistant](https://cla-assistant.percona.com/readme/badge/percona/telemetry-agent)](https://cla-assistant.percona.com/percona/telemetry-agent)
[![Go Report Card](https://goreportcard.com/badge/github.com/percona/telemetry-agent)](https://goreportcard.com/report/github.com/percona/telemetry-agent)

<!-- TOC -->
* [Percona Telemetry](#percona-telemetry)
  * [Installation-time telemetry](#installation-time-telemetry)
    * [Disable installation-time telemetry](#disable-installation-time-telemetry)
  * [Continuous telemetry](#continuous-telemetry)
    * [Elements of the continuous telemetry system](#elements-of-the-continuous-telemetry-system)
    * [Locations of metrics files and telemetry history](#locations-of-metrics-files-and-telemetry-history)
    * [Metrics file format](#metrics-file-format)
    * [Percona Telemetry Agent](#percona-telemetry-agent)
      * [Telemetry agent payload example](#telemetry-agent-payload-example)
      * [Telemetry Agent configuration](#telemetry-agent-configuration)
    * [Disable continuous telemetry](#disable-continuous-telemetry)
      * [Disable the Telemetry Agent](#disable-the-telemetry-agent)
        * [Disable temporarily](#disable-temporarily)
        * [Disable permanently](#disable-permanently)
      * [Disable DB component](#disable-db-component)
<!-- TOC -->

This repository contains the Percona Telemetry Agent for Pillars telemetry project, a tool that collects telemetry 
information and sends it to Percona Telemetry service.

For the time being Pillars (Percona Server for MySQL, Percona Server for MongoDB, Percona Server for PostgreSQL) 
Telemetry consists of the following parts:
* [Installation-time telemetry](#installation-time-telemetry)
* [Continuous telemetry](#continuous-telemetry)

All telemetry data is sent to the Percona Telemetry service. The service is responsible for storing and processing the
data. The data is used to improve the quality of Percona products and services.
Telemetry data is sent to https://check.percona.com/v1/telemetry/GenericReport endpoint in a JSON format.

## Installation-time telemetry

This feature is enabled in Percona Linux packages and Docker containers by default. In order to disable it see 
[Disable installation-time telemetry](#disable-installation-time-telemetry)

This telemetry is executed only once during software installation. It collects information at the moment of installation 
or Docker container startup and does not run afterward.

For this purpose the script `call-home.sh` is used that collects telemetry information and sends it to a Percona Telemetry service.
The script validates only if mandatory parameters are provided. It does not check the validity and itegritiy of provided parameters.

Usage: 
```{.bash data-prompt="$"}
./call-home.sh OPTIONS
OPTIONS can be:
  -h  Show this message
  -f  [PERCONA_PRODUCT_FAMILY]              Product family identifier.                                  [REQUIRED]
  -v  [PERCONA_PRODUCT_VERSION]             Product version.                                            [REQUIRED]
  -s  [PERCONA_OPERATING_SYSTEM]            Operating system identifier.                                [Default: autodetected with fallback to "unknown"]
  -d  [PERCONA_DEPLOYMENT_METHOD]           Deployment method.                                          [REQUIRED]
  -i  [PERCONA_INSTANCE_ID]                 Instance id                                                 [Default: autogenerated]
  -j  [PERCONA_TELEMETRY_CONFIG_FILE_PATH]  Path of the file where to store the unique ID of this node. [Default: /usr/local/percona/telemetry_uuid]
  -u  [PERCONA_TELEMETRY_URL]               Percona Telemetry Service endpoint                          [Default: https://check.percona.com/v1/telemetry/GenericReport]
  -c  [PERCONA_CONNECT_TIMEOUT]             Default timeout for the curl to establish connection.       [Default: 5]
  -t  [PERCONA_SEND_TIMEOUT]                Default timeout for the whole curl command.                 [Default: 10]
```

Note that `-d PERCONA_PRODUCT_FAMILY` can be set to any string, but only the following ones will be accepted
by Percona Telemetry service (there is no validation of the script side):
```
PRODUCT_FAMILY_PS
PRODUCT_FAMILY_PXC
PRODUCT_FAMILY_PXB
PRODUCT_FAMILY_PSMDB
PRODUCT_FAMILY_PBM
PRODUCT_FAMILY_POSTGRESQL
PRODUCT_FAMILY_PMM
PRODUCT_FAMILY_EVEREST
PRODUCT_FAMILY_PERCONA_TOOLKIT
```

For example, on Debian-derived distribution, you may run the script as:
```{.bash data-prompt="$"}
./call-home.sh -f "PRODUCT_FAMILY_PS" -v "8.0.33" -s "$(cat /etc/issue)" -i "13f5fc62-35b4-4716-b3e6-96c761fc204d" -j /tmp/percona.telemetry -u https://check.percona.com/v1/telemetry/GenericReport -c 1 -t 2
```

on a Red Hat-derived distribution, you may run the script as:
```{.bash data-prompt="$"}
./call-home.sh -f "PRODUCT_FAMILY_PS" -v "8.0.33" -s "$(cat /etc/redhat-release)" -i "13f5fc62-35b4-4716-b3e6-96c761fc204d" -j /tmp/percona.telemetry -u https://check.percona.com/v1/telemetry/GenericReport -c 1 -t 2
```

### Disable installation-time telemetry

The data collection may be disabled via setting an environment variable `PERCONA_TELEMETRY_DISABLE=1` during Linux package 
installation or Docker container startup.

For example, on Debian-derived distribution (this action does not affect the continuous telemetry part):
```{.bash data-prompt="$"}
sudo PERCONA_TELEMETRY_DISABLE=1 apt install percona-server-server
```

on a Red Hat-derived distribution (this action does not affect the continuous telemetry part):
```{.bash data-prompt="$"}
sudo PERCONA_TELEMETRY_DISABLE=1 dnf install percona-server-server
```

or in a Docker container (this action disables the continuous telemetry part as well):
```{.bash data-prompt="$"}
docker run -e PERCONA_TELEMETRY_DISABLE=1 percona/percona-server
```

## Continuous telemetry

This telemetry part involves setting up a Telemetry Agent and a database (DB) component. It continuously collects and 
sends information daily.

The Telemetry Agent runs at scheduled daily intervals to collect data. The agent gathers data (for example, usage statistics) 
and sends this information to the Percona Telemetry Service.

### Elements of the continuous telemetry system

Percona collects information using these elements:

| Function                                                          | Description                                                                                                                                                                                                                                                                                                                                                 |
|-------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Percona Telemetry DB component                                    | This component collects metrics directly from the database and stores them in a metrics file.                                                                                                                                                                                                                                                               |
| [Metrics File](#locations-of-metrics-files-and-telemetry-history) | This standalone file on the database host's file system stores the collected metrics.                                                                                                                                                                                                                                                                       |
| [Telemetry Agent](#percona-telemetry-agent)                       | This independent process runs on your database host's operating system and performs the following tasks:<br> - Collects OS-level metrics.<br>- Reads the metrics file and adds the OS-level metrics.<br>- Sends the complete set of metrics to the Percona Platform.<br> - Collects the list of installed Percona packages using the local package manager. |

### Locations of metrics files and telemetry history

Percona stores the Metrics file in one of the following directories on the local file system. The location depends on the product.

* Telemetry root path - `/usr/local/percona/telemetry`
* PSMDB (mongod) root path -   `${telemetry root path}/psmdb/`
* PSMDB (mongos) root path - `${telemetry root path}/psmdbs/`
* PS root path -   `${telemetry root path}/ps/`
* PXC root path - `${telemetry root path}/pxc/`
* PG root path - `${telemetry root path}/pg/`

Percona archives the telemetry history in `${telemetry root path}/history/`.

### Metrics file format

The Metrics file uses the Javascript Object Notation (JSON) format. Percona reserves the right to extend the current set 
of JSON structure attributes in the future.

An example of the Metrics file content is the following:

 ```json
 {
   "db_instance_id": "e83c568c-e140-11ee-8320-7e207666b18a",
   "pillar_version": "8.0.35-27",
   "active_plugins": [
     "binlog",
     "mysql_native_password",
     "sha256_password",
     "caching_sha2_password",
     "sha2_cache_cleaner",
     "daemon_keyring_proxy_plugin",
     "PERFORMANCE_SCHEMA",
     "ROCKSDB_INDEX_FILE_MAP",
     "ROCKSDB_LOCKS",
     "ROCKSDB_TRX",
     "ROCKSDB_DEADLOCK"
   ],
   "active_components": [
     "file://component_percona_telemetry"
   ],
   "uptime": "6185",
   "databases_count": "7",
   "databases_size": "33149",
   "se_engines_in_use": [
     "InnoDB",
     "ROCKSDB"
   ],
   "replication_info": {
     "is_semisync_source": "1",
     "is_replica": "1"
   }
 }
 ```

### Percona Telemetry Agent

This program, called `percona-telemetry-agent`, constantly runs in the background on your server's host system. 
It manages JSON files, which store the collected data in a specific location (`${telemetry root path}`). This agent can 
create, read, write, and delete these files.
The agent's log file, containing information about its activity, is located at `/var/log/percona/telemetry-agent.log`.

In the first 24 hours, no information is collected or sent. After that period, the agent tries to send the collected 
information to Percona Telemetry Service daily. If this operation fails, the agent retries up to five times. 
After the data is successfully sent, the agent saves a copy of the sent data in a separate "history" folder 
(`${telemetry root path}/history/`), and then, deletes the original file created by the database.

The agent won't send any data if the target directory doesn't contain specific files related to Percona software.

#### Telemetry agent payload example

The following is an example of a Telemetry Agent payload:

 ```json
 {
   "reports": [
     {
       "id": "B5BDC47B-B717-4EF5-AEDF-41A17C9C18BB",
       "createTime": "2023-09-01T10:56:49Z",
       "instanceId": "B5BDC47B-B717-4EF5-AEDF-41A17C9C18BA",
       "productFamily": "PRODUCT_FAMILY_PS",
       "metrics": [
         {
           "key": "OS",
           "value": "Ubuntu"
         },
         {
           "key": "pillar_version",
           "value": "8.0.33-25"
         }
       ]
     }
   ]
 }
 ```

The agent sends information about the database and metrics.

| Key           | Description                                                                                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| id            | A randomly generated Universally Unique Identifier (UUID) version 4 of request                                                                                    |
| createTime    | UNIX timestamp of request creation                                                                                                                                |
| instanceId    | The DB Host ID. The value can be taken from the `instanceId`, the `/usr/local/percona/telemetry_uuid`<br/> or generated as a UUID version 4 if the file is absent |
| productFamily | The value from the file path                                                                                                                                      |
| metrics       | An array of key:value pairs collected from the Metrics file                                                                                                       |

The following operating system-level metrics are sent with each metrics send iteration:

| Key                  | Description                                                                                |
|----------------------|--------------------------------------------------------------------------------------------|
| "OS"                 | The name of the operating system                                                           |
| "hardware_arch"      | CPU architecture used on DB host                                                           |
| "deployment"         | How the application was deployed. <br> The possible values could be "PACKAGE" or "DOCKER". |
| "installed_packages" | A list of the installed Percona's packages.                                                |

#### Telemetry Agent configuration

Telemetry Agent can be configured during startup by setting the following environment variables or their CLI arguments equivalents:

| Environment variable                    | CLI param                         | Description                                                     | Default value                                        |
|-----------------------------------------|-----------------------------------|-----------------------------------------------------------------|------------------------------------------------------|
| PERCONA_TELEMETRY_ROOT_PATH             | --telemetry.root-path             | The root path for telemetry files                               | /usr/local/percona/telemetry                         |
| PERCONA_TELEMETRY_CHECK_INTERVAL        | --telemetry.check-interval        | The interval in seconds between telemetry checks                | 86400                                                |
| PERCONA_TELEMETRY_RESEND_INTERVAL       | --telemetry.resend-interval       | The interval in seconds between telemetry resend attempts       | 60                                                   |
| PERCONA_TELEMETRY_HISTORY_KEEP_INTERVAL | --telemetry.history-keep-interval | The interval in seconds between telemetry history files cleanup | 604800                                               |
| PERCONA_TELEMETRY_URL                   | --telemetry.url                   | The URL of the Percona Telemetry Service                        | https://check.percona.com/v1/telemetry/GenericReport |
|                                         | --log.verbose                     | Enable verbose logging                                          | false                                                |
|                                         | --log.dev-mode                    | Enable development mode                                         | false                                                |
|                                         | --version                         | Print version and exit                                          | false                                                |
|                                         | --help                            | Show help                                                       | false                                                |

Changing any of this configuration parameters requires a restart of the Telemetry Agent.

### Disable continuous telemetry

Percona software enables the continuous telemetry system by default. Disable the Telemetry agent and uninstall the DB 
component to turn off this telemetry completely.

These actions do not affect [Installation-time telemetry](#installation-time-telemetry).

#### Disable the Telemetry Agent

You can either disable the Telemetry agent for a session or permanently. These actions do not affect the DB component, i.e.
DB will still continue collecting metrics but they will not be sent to Percona Telemetry Service. 

##### Disable temporarily

Turn off Telemetry Agent temporarily until the next server restart:
 ```{.bash data-prompt=$}
 systemctl stop percona-telemetry-agent
 ```

##### Disable permanently

Turn off Telemetry Agent permanently:
 ```{.bash data-prompt=$}
 systemctl stop percona-telemetry-agent
 systemctl disable percona-telemetry-agent
 ```

#### Disable DB component

The DB component continues to generate daily telemetry files and store them for a week, even after you stop the 
Telemetry Agent service.
Refer to particular Percona DB server documentation in order to disable the DB component.