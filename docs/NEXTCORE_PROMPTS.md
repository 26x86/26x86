# NextCore Prompts (User Flow Slot)

## Responsibility

This specification defines the user-facing wizard flow, selection options, and diagnostic copy for the NextCore setup tool. Functional mechanics are governed by Design and Build Plan specifications.

## Principles

- **Documentation & UI Language: English Only.**
  All text, wizard prompts, CLI help strings, button labels, and diagnostic explanations must be presented in **English**.
- **Evidence-Based Messaging:**
  The UI must clearly distinguish simulated/offline validation from live physical macOS boot verification.
- **Concise, Professional Tone:**
  User-facing messages should be actionable, clear, and free of internal engineering jargon where possible.

## Wizard Step Progression

1. **Step 1: Welcome & Overview**
   - Title: Welcome to NextCore
   - Description: NextCore configures clean-room EFI boot environments for macOS on x86-based Mac hardware.
2. **Step 2: Hardware Detection**
   - Displays detected CPU model, AVX instruction support, GPU classification, and SMBIOS identity.
3. **Step 3: Target Configuration**
   - Allows selecting target macOS release and target storage disk.
4. **Step 4: Build & Installation**
   - Assembles declarative `config.plist` and EFI folder hierarchy on the designated EFI system partition.
5. **Step 5: Completion & Instructions**
   - Informs the user that installation is complete and outlines reboot instructions (holding Option to select EFI Boot).
