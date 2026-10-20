#define MICROPY_HW_BOARD_NAME       "CMG2-F205"
#define MICROPY_HW_MCU_NAME         "STM32F205RG"

// 系统时钟 = 24 MHz HSE * 8 / 3 = 72 MHz (F205 安全区间)
#define MICROPY_HW_CLK_PLLM         (12)   // 24 MHz / 12 = 2 MHz
#define MICROPY_HW_CLK_PLLN         (216)
#define MICROPY_HW_CLK_PLLP         (RCC_PLLP_DIV2)   // 216 / 2 = 108 MHz
#define MICROPY_HW_CLK_PLLQ         (9)               // USB 需要 48 MHz：216 / 9 = 48
#define MICROPY_HW_CLK_LAST_FREQ    (108000000)

// 1 MBit 内置 Flash，默认 1 M / 16 k = 64 页
#define MICROPY_HW_FLASH_SIZE       (1024 * 1024)
#define MICROPY_HW_FLASH_LATENCY    FLASH_LATENCY_3   // 108 MHz 时 3WS

// USB-FS 引脚
#define MICROPY_HW_USB_FS              (1)
#define MICROPY_HW_USB_VBUS_DETECT_PIN (pin_A9)   // 如果 VBUS 没连，可以改成 NO_VBUS
#define MICROPY_HW_USB_ID_PIN          (pin_A10)  // 如果 ID 没连，可注释掉

// 用户 LED
#define MICROPY_HW_LED1             (pin_A8)   // 低电平点亮
#define MICROPY_HW_LED_ON(pin)      mp_hal_pin_low(pin)
#define MICROPY_HW_LED_OFF(pin)     mp_hal_pin_high(pin)

// I2C1 映射到你原理图的 PA6/PA7
#define MICROPY_HW_I2C1_SCL         (pin_A7)
#define MICROPY_HW_I2C1_SDA         (pin_A6)

// 如果没有外部 32 kHz 晶振，把 RTC 时钟源设成 LSI
#define MICROPY_HW_RTC_USE_LSE      (0)