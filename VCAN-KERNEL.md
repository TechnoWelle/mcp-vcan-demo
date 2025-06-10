# **🧰 Building a Custom WSL2 Kernel with Built-in VCAN Support**
This guide explains how to build a custom Microsoft WSL2 kernel based on **Linux v6.6.x**, and how to **embed the VCAN (Virtual CAN) driver directly into the kernel**, so it is available out-of-the-box in all WSL2 distributions.

-----
## **📦 Prerequisites**
Ensure you have the following installed in your WSL2 Ubuntu environment:

```shell
sudo apt update && sudo apt install -y \
build-essential flex bison libssl-dev libelf-dev \
bc python3 pahole cpio git libncurses-dev
```

-----
## **🧬 Clone the WSL2 Kernel Source**
Clone the Microsoft WSL2 kernel source targeting the 6.6 branch:

```shell
git clone https://github.com/microsoft/WSL2-Linux-Kernel.git --depth=1 -b linux-msft-wsl-6.6.y

cd WSL2-Linux-Kernel
```

-----
## **🛠️ Enable VCAN as a Built-in Kernel Feature**
We'll now modify the kernel configuration to build vcan **into** the kernel instead of as a module.
### **1. Launch Kernel Configuration**
```shell
make menuconfig KCONFIG_CONFIG=Microsoft/config-wsl
```
This opens an interactive configuration menu using the config-wsl file as a base.
### **2. Enable VCAN Support**
Navigate through the following menu structure:

Device Drivers  --->

`  `Network device support  --->

`    `<\*> Virtual CAN interface (vcan)

✅ Ensure vcan is marked with \* (**built-in**) instead of M (module).

Press / and search for vcan if you want a shortcut.
### **3. Save and Exit**
- Save the changes when prompted.
-----
## **⚙️ Build the Kernel**
Use all available cores to speed up compilation:

```shell
make -j$(nproc) KCONFIG_CONFIG=Microsoft/config-wsl
```
-----
## **📁 Copy Kernel Image to Windows**
After the build completes, copy the kernel image (bzImage) to a location accessible by Windows:

```shell
cp arch/x86/boot/bzImage /mnt/c/WSL-CustomKernel/bzImage
```

Create the folder on the Windows side first (e.g., C:\WSL-CustomKernel).

-----
## **🧩 Configure WSL2 to Use the Custom Kernel**
1. Open or create the WSL configuration file:

   ```powershell
   %USERPROFILE%\.wslconfig
   ```

1. Add the following content (adjust path as needed):

   [wsl2]

   kernel = C:\\WSL-CustomKernel\\bzImage

-----
## **🔄 Restart WSL**
Restart the WSL2 engine for changes to take effect:

```shell
wsl --shutdown
```

Launch any WSL2 distribution again.

-----
## **✅ Verify VCAN Availability**
In your WSL2 terminal, run:

```shell
sudo ip link add dev vcan0 type vcan

sudo ip link set up vcan0

ip a show vcan0
```

You should see the vcan0 interface available. Also, verify that vcan is **built-in** by checking that it **does not appear in** lsmod:

```shell
lsmod | grep vcan
```

If no output appears, it confirms vcan is built into the kernel.

-----
## **🧪 Optional: Add Other CAN Modules**
You can repeat the steps above to embed other CAN-related features:

- can
- can\_raw
- slcan
- vcan
- can\_dev

Look for these options under:

Networking support  --->

`  `CAN bus subsystem support  --->

-----
## **📌 Summary**

|**Feature**|**Status**|
| :-: | :-: |
|Kernel Base|Microsoft WSL 6.6.y|
|VCAN|Built into kernel|
|Distributions|All WSL2 distros use same kernel|
|Persistence|Works after reboot and WSL restart|
## **References:**
<https://learn.microsoft.com/en-us/community/content/wsl-user-msft-kernel-v6>
