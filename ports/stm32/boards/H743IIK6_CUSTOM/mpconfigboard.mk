USE_MBOOT ?= 0

# MCU 系列
MCU_SERIES = h7
CMSIS_MCU = STM32H743xx

# 链接脚本（不用 Mboot，直接 0x08020000 开始）
LD_FILES = boards/stm32h743.ld boards/common_basic.ld
TEXT0_ADDR = 0x08000000

# 引脚表
AF_FILE = boards/stm32h743_af.csv

# 打开常用模块
MICROPY_PY_LWIP = 0        # 没有 PHY 先关掉
MICROPY_PY_SSL = 1
MICROPY_SSL_MBEDTLS = 1
MICROPY_VFS_LFS2 = 1
MICROPY_PY_BTREE = 0       # 省空间

MICROPY_HW_ENABLE_USB      = 1
MICROPY_HW_ENABLE_TINYUSB  = 1
MICROPY_HW_USB_CDC         = 1

# 冻结清单（可先空着）
FROZEN_MANIFEST ?= $(BOARD_DIR)/manifest.py