# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0beta] - 2024-09-28
### Added support for Promethus/Grafana
- Added support for Promethus/Grafana

## [1.0.8] - 2024-09-15
### Added/Bugfix
- CI/CD pipeline for internal dev
- Fixed docker file and docker compose file to use USB UPS
- Added reset_engine API REST

## [1.0.7] - 2024-08-10
### Added
- Added Mibu Component/Flow Diagram in README file
- Removed exposed docker port for Mongo and Redis  

## [1.0.6] - 2024-07-09
### Bugfix
- Fixed nginx configuration

## [1.0.5] - 2024-07-04
### Added
- Added support for docker
- Project files structure refactored

## [1.0.4] - 2024-07-04
### Bugfix
- Bugfix for USB UPS device with Linux OS

## [1.0.3] - 2024-07-01
### Added
- New log script to be able to archive the old logs
- Front end lightly updated

## [1.0.2] - 2024-06-24
### Added
- Fixed the logs for linux OS
- Added timeout for the Workers

## [1.0.1] - 2024-06-15
### Added
- Added this `CHANGELOG.md` file
- Fixed the default log/lock file paths in the `config_loader.py`
- Added the missing retry library in the `requirements.txt`

## [1.0.0] - 05-31-2024
### Added
- Initial creation of the project
- In this first version , Mibu can communicate with Dell and Cisco servers, Fortinet firewalls, and CyberPower UPS systems.



