import spidev
import RPi.GPIO as GPIO
import time

class MCP3208:
    def __init__(self, vcc, cs_pin_no, ref_millivolt):
        self.vcc = vcc
        self.cs_pin_no = cs_pin_no
        self.ref_millivolt = ref_millivolt
        self.spi = spidev.SpiDev()

    def adc_init(self):
        # SPIバスとデバイス番号 (通常、bus=0, device=0)
        self.spi.open(0, 0)
        self.spi.max_speed_hz = 2000000 if self.vcc == 5 else 1000000
        self.spi.mode = 0b00

        # GPIOの設定
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.cs_pin_no, GPIO.OUT)
        GPIO.output(self.cs_pin_no, GPIO.HIGH)

    def read_adc(self, channel):
        if channel < 0 or channel > 7:
            raise ValueError("チャネル番号は 0〜7 の範囲で指定してください。")
        
        GPIO.output(self.cs_pin_no, GPIO.LOW)
        adc = self.spi.xfer2([
            0b00000110 | (channel >> 2),         # Start bit + Single/Diff + D2
            (channel & 0x03) << 6,               # D1 + D0 + 6 zeros
            0x00                                 # 8 zeros
        ])
        GPIO.output(self.cs_pin_no, GPIO.HIGH)

        result = ((adc[1] & 0x0F) << 8) | adc[2]
        return result

    def read_millivolt(self, channel):
        adc_value = self.read_adc(channel)
        return int((self.ref_millivolt * adc_value) / 4095.0)

    def close(self):
        self.spi.close()
        GPIO.cleanup()

# ======== 使用例 ========
if __name__ == "__main__":
    try:
        mcp = MCP3208(vcc=5, cs_pin_no=8, ref_millivolt=5000)  # CSピンGPIO8 (BCM番号)
        mcp.adc_init()

        while True:
            raw = mcp.read_adc(0)  # チャネル0
            mv = mcp.read_millivolt(0)
            print(f"ADC Raw: {raw}, Voltage: {mv} mV")
            time.sleep(1)

    except KeyboardInterrupt:
        print("終了します")

    finally:
        mcp.close()
