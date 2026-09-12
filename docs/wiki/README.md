# NextCore documentation

**Current Status:** Public guide index; installation and runtime readiness remain separate.

**Target State:** Accurate, reproducible guidance tied to the specific source, hardware and execution layer.

This guide index complements the [documentation portal](../index.md). Start with
[compatibility](../compatibility.md) and [current progress](../progress.md), then
choose application setup, external OpenCore preparation or experimental NextCore
firmware development. The [library](../library.md) indexes specifications.
A documentation target is not a verified installation path.

## Introduction

| Topic | Document |
| --- | --- |
| New to NextCore | [Getting started](Getting-Started.md) |
| What is OpenCore in this project? | [OpenCore](OpenCore.md) |
| Which Macs are covered? | [Supported models](Supported-Models.md) |
| Frequently asked questions | [Troubleshooting](Troubleshooting.md) |

## Preparation and installation boundaries

| Topic | Document |
| --- | --- |
| Prepare an installer and backup | [Getting started](Getting-Started.md) |
| Build and install the EFI | [OpenCore](OpenCore.md) |
| Installation evidence requirements | [Installation notes](Installation-Notes.md) |
| Configure device-specific options | [Configuration](Configuration.md) |

## macOS support

| Topic | Document |
| --- | --- |
| Tahoe and newer macOS work | [macOS support](macOS-Support.md) |
| Pre-AVX Mac Pro constraints | [Pre-AVX Mac Pro](Pre-AVX-Mac-Pro.md) |

## Application

| Topic | Document |
| --- | --- |
| Guided workflow and modes | [Application](Application.md) |
| Updating and rollback | [Migration](Migration.md) |
| OpenCore package inventory | [Upstream repositories](Upstream-Repositories.md) |

## Troubleshooting

| Topic | Document |
| --- | --- |
| Start with the evidence layer | [Troubleshooting](Troubleshooting.md) |
| Boot, installer, and EFI issues | [Known issues](Known-Issues.md) |
| GPU and non-Metal issues | [GPU limitations](GPU-Limitations.md) |
| Warnings before changing a live system | [Warnings](Warnings.md) |

## Developer documentation

| Topic | Document |
| --- | --- |
| Public architecture | [Architecture](Architecture.md) |
| Build and development | [Build and development](Build-and-Development.md) |
| NextCore design | [NextCore design](../NEXTCORE_DESIGN.md) |
| Build plan and validation | [NextCore build plan](../NEXTCORE_BUILD_PLAN.md) |
| Public/private boundary | [Privacy and disclosure](Privacy-and-Disclosure.md) |

Internal research material and implementation details are intentionally not
indexed here. Public documentation must remain sufficient for use without
revealing private project names, source, or isolated research assets.
