#include "py/mphal.h"
#include "pin.h"

void board_init(void) {
    // 上电先灭灯（输出高）
    mp_hal_pin_output(pin_C0);
    mp_hal_pin_output(pin_C1);
    mp_hal_pin_output(pin_C2);
    mp_hal_pin_write(pin_C0, 1);
    mp_hal_pin_write(pin_C1, 1);
    mp_hal_pin_write(pin_C2, 1);
}

void board_init(void) {
    mp_hal_pin_output(pin_C0);
    for (int i = 0; i < 60; i++) {   // 上电快闪 3 次
        mp_hal_pin_toggle(pin_C0);
        mp_hal_delay_ms(500);
    }
    mp_hal_pin_write(pin_C1, 0);    // 结束常灭
    mp_hal_pin_output(pin_C1);
    for (int i = 0; i < 60; i++) {   // 上电快闪 3 次
        mp_hal_pin_toggle(pin_C1);
        mp_hal_delay_ms(500);
    }
    mp_hal_pin_write(pin_C0, 0);    // 结束常灭
    mp_hal_pin_output(pin_C2);
    for (int i = 0; i < 60; i++) {   // 上电快闪 3 次
        mp_hal_pin_toggle(pin_C2);
        mp_hal_delay_ms(500);
    }
    mp_hal_pin_write(pin_C2, 0);    // 结束常灭

}