// -------- 板名/芯片名 --------
#define MICROPY_HW_BOARD_NAME       "H743IIK6-USB-CDC"
#define MICROPY_HW_MCU_NAME         "STM32H743IIK6"

// -------- Flash 布局 --------
#define FLASH_APP_START             0x08000000   // 留给 DFU bootloader 128 kB
#define FLASH_PAGE_SIZE             0x20000

// -------- 时钟：12 MHz 无源晶振 --------
#define HSE_VALUE                   (12000000)

// -------- USB-FS（内置 PHY） --------
#define MICROPY_HW_USB_FS           (1)          // 用 PA11/12

// -------- PLL 系数：12 MHz → 480 MHz --------
#define MICROPY_HW_CLK_PLLM         (12)
#define MICROPY_HW_CLK_PLLN         (480)
#define MICROPY_HW_CLK_PLLP         (2)
#define MICROPY_HW_CLK_PLLQ         (10)         // USB 48 MHz
#define MICROPY_HW_CLK_PLLR         (2)
#define MICROPY_HW_CLK_PLLVCI       (RCC_PLL1VCIRANGE_2)
#define MICROPY_HW_CLK_PLLVCO       (RCC_PLL1VCOWIDE)
#define MICROPY_HW_CLK_PLLFRAC      (0)

// -------- USB-CDC 虚拟串口 --------
#define MICROPY_HW_USB_CDC          (1)          // 启用 CDC-ACM
// 不需要真实 UART 脚，因此把 UART1 定义全部删掉（或留空）


// 删掉重复的 USB_FS 定义，只保留：
#define MICROPY_HW_USB_OTG2_FS      (1)   // H7 用 OTG2-FS
#define MICROPY_HW_USB_CDC          (1)
// 强制设备模式，不检测 VBUS
#define MICROPY_HW_USB_VBUS_SENSE_PIN        (0)
#define MICROPY_HW_USB_OTG_FS_VBUS_SENSE_PIN (0)
// USB
#define MICROPY_HW_USB_FS           (1)
#define MICROPY_HW_USB_CDC          (1)
#define MICROPY_HW_USB_OTG2_FS      (1)   // H7 必须用 OTG2-FS


// -------- 板载 RGB LED --------
#define MICROPY_HW_LED1             (pin_C0)   // R
#define MICROPY_HW_LED2             (pin_C1)   // G  
#define MICROPY_HW_LED3             (pin_C2)   // B
// 1 = 低电平点亮（根据你板子实际改）
#define MICROPY_HW_LED1_INVERTED    (1)
#define MICROPY_HW_LED2_INVERTED    (1)
#define MICROPY_HW_LED3_INVERTED    (1)


// -------- LED 电平逻辑 --------
#define MICROPY_HW_LED_ON(p)      mp_hal_pin_write((p), 0)   // 低电平点亮
#define MICROPY_HW_LED_OFF(p)     mp_hal_pin_write((p), 1)   // 高电平熄灭

// -------- OTG2-FS 时钟 & IRQ --------
#define MICROPY_HW_USB_OTG2_HS_ULPI (0)   // 不用 ULPI
#define MICROPY_HW_USB_OTG2_FS      (1)   // 用内置 FS
#define MICROPY_HW_USB_FS_NUM       (1)   // 控制器编号 1 = OTG2
