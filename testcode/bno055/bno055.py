# このコードはSC25のコードをコピーしたものです
# このコードは以下のコードが元となっています
# https://github.com/adafruit/Adafruit_Python_BNO055/blob/master/Adafruit_BNO055/BNO055.py
# 以下の条件のもと，利用することができます．

# Adafruit BNO055 Absolute Orientation Sensor Library
# Copyright (c) 2015 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# このコードの動かし方
# 1. ラズパイを起動
# 2. ターミナル(黒い画面)を開く
# 3. 次のコマンドを実行
#   cd ~/sc26_project
#   .  sc26_env/bin/activate           <==必ず実行！！！ 仮想環境に入る
#   sudo pigpiod                       <==必ず実行！！！ pigpioデーモンを起動
#   cd SC-26
#   git pull
#   python testcode/bno055/bno055.py


# import binascii  # UARTによる通信を行うときのみ使用
from logging import getLogger, StreamHandler  # ログを記録するため
import time

import pigpio
# import serial  # UARTによる通信を行うときに使用

# import calc_goal  # ゴールまでの距離と方向を計算

# I2C addresses
BNO055_ADDRESS_A                     = 0x28
BNO055_ADDRESS_B                     = 0x29
BNO055_ID                            = 0xA0

# Page id register definition
BNO055_PAGE_ID_ADDR                  = 0X07

# PAGE0 REGISTER DEFINITION START
BNO055_CHIP_ID_ADDR                  = 0x00
BNO055_ACCEL_REV_ID_ADDR             = 0x01
BNO055_MAG_REV_ID_ADDR               = 0x02
BNO055_GYRO_REV_ID_ADDR              = 0x03
BNO055_SW_REV_ID_LSB_ADDR            = 0x04
BNO055_SW_REV_ID_MSB_ADDR            = 0x05
BNO055_BL_REV_ID_ADDR                = 0X06

# Accel data register
BNO055_ACCEL_DATA_X_LSB_ADDR         = 0X08
BNO055_ACCEL_DATA_X_MSB_ADDR         = 0X09
BNO055_ACCEL_DATA_Y_LSB_ADDR         = 0X0A
BNO055_ACCEL_DATA_Y_MSB_ADDR         = 0X0B
BNO055_ACCEL_DATA_Z_LSB_ADDR         = 0X0C
BNO055_ACCEL_DATA_Z_MSB_ADDR         = 0X0D

# Mag data register
BNO055_MAG_DATA_X_LSB_ADDR           = 0X0E
BNO055_MAG_DATA_X_MSB_ADDR           = 0X0F
BNO055_MAG_DATA_Y_LSB_ADDR           = 0X10
BNO055_MAG_DATA_Y_MSB_ADDR           = 0X11
BNO055_MAG_DATA_Z_LSB_ADDR           = 0X12
BNO055_MAG_DATA_Z_MSB_ADDR           = 0X13

# Gyro data registers
BNO055_GYRO_DATA_X_LSB_ADDR          = 0X14
BNO055_GYRO_DATA_X_MSB_ADDR          = 0X15
BNO055_GYRO_DATA_Y_LSB_ADDR          = 0X16
BNO055_GYRO_DATA_Y_MSB_ADDR          = 0X17
BNO055_GYRO_DATA_Z_LSB_ADDR          = 0X18
BNO055_GYRO_DATA_Z_MSB_ADDR          = 0X19

# Euler data registers
BNO055_EULER_H_LSB_ADDR              = 0X1A
BNO055_EULER_H_MSB_ADDR              = 0X1B
BNO055_EULER_R_LSB_ADDR              = 0X1C
BNO055_EULER_R_MSB_ADDR              = 0X1D
BNO055_EULER_P_LSB_ADDR              = 0X1E
BNO055_EULER_P_MSB_ADDR              = 0X1F

# Quaternion data registers
BNO055_QUATERNION_DATA_W_LSB_ADDR    = 0X20
BNO055_QUATERNION_DATA_W_MSB_ADDR    = 0X21
BNO055_QUATERNION_DATA_X_LSB_ADDR    = 0X22
BNO055_QUATERNION_DATA_X_MSB_ADDR    = 0X23
BNO055_QUATERNION_DATA_Y_LSB_ADDR    = 0X24
BNO055_QUATERNION_DATA_Y_MSB_ADDR    = 0X25
BNO055_QUATERNION_DATA_Z_LSB_ADDR    = 0X26
BNO055_QUATERNION_DATA_Z_MSB_ADDR    = 0X27

# Linear acceleration data registers
BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR  = 0X28
BNO055_LINEAR_ACCEL_DATA_X_MSB_ADDR  = 0X29
BNO055_LINEAR_ACCEL_DATA_Y_LSB_ADDR  = 0X2A
BNO055_LINEAR_ACCEL_DATA_Y_MSB_ADDR  = 0X2B
BNO055_LINEAR_ACCEL_DATA_Z_LSB_ADDR  = 0X2C
BNO055_LINEAR_ACCEL_DATA_Z_MSB_ADDR  = 0X2D

# Gravity data registers
BNO055_GRAVITY_DATA_X_LSB_ADDR       = 0X2E
BNO055_GRAVITY_DATA_X_MSB_ADDR       = 0X2F
BNO055_GRAVITY_DATA_Y_LSB_ADDR       = 0X30
BNO055_GRAVITY_DATA_Y_MSB_ADDR       = 0X31
BNO055_GRAVITY_DATA_Z_LSB_ADDR       = 0X32
BNO055_GRAVITY_DATA_Z_MSB_ADDR       = 0X33

# Temperature data register
BNO055_TEMP_ADDR                     = 0X34

# Status registers
BNO055_CALIB_STAT_ADDR               = 0X35
BNO055_SELFTEST_RESULT_ADDR          = 0X36
BNO055_INTR_STAT_ADDR                = 0X37

BNO055_SYS_CLK_STAT_ADDR             = 0X38
BNO055_SYS_STAT_ADDR                 = 0X39
BNO055_SYS_ERR_ADDR                  = 0X3A

# Unit selection register
BNO055_UNIT_SEL_ADDR                 = 0X3B
BNO055_DATA_SELECT_ADDR              = 0X3C

# Mode registers
BNO055_OPR_MODE_ADDR                 = 0X3D
BNO055_PWR_MODE_ADDR                 = 0X3E

BNO055_SYS_TRIGGER_ADDR              = 0X3F
BNO055_TEMP_SOURCE_ADDR              = 0X40

# Axis remap registers
BNO055_AXIS_MAP_CONFIG_ADDR          = 0X41
BNO055_AXIS_MAP_SIGN_ADDR            = 0X42

# Axis remap values
AXIS_REMAP_X                         = 0x00
AXIS_REMAP_Y                         = 0x01
AXIS_REMAP_Z                         = 0x02
AXIS_REMAP_POSITIVE                  = 0x00
AXIS_REMAP_NEGATIVE                  = 0x01

# SIC registers
BNO055_SIC_MATRIX_0_LSB_ADDR         = 0X43
BNO055_SIC_MATRIX_0_MSB_ADDR         = 0X44
BNO055_SIC_MATRIX_1_LSB_ADDR         = 0X45
BNO055_SIC_MATRIX_1_MSB_ADDR         = 0X46
BNO055_SIC_MATRIX_2_LSB_ADDR         = 0X47
BNO055_SIC_MATRIX_2_MSB_ADDR         = 0X48
BNO055_SIC_MATRIX_3_LSB_ADDR         = 0X49
BNO055_SIC_MATRIX_3_MSB_ADDR         = 0X4A
BNO055_SIC_MATRIX_4_LSB_ADDR         = 0X4B
BNO055_SIC_MATRIX_4_MSB_ADDR         = 0X4C
BNO055_SIC_MATRIX_5_LSB_ADDR         = 0X4D
BNO055_SIC_MATRIX_5_MSB_ADDR         = 0X4E
BNO055_SIC_MATRIX_6_LSB_ADDR         = 0X4F
BNO055_SIC_MATRIX_6_MSB_ADDR         = 0X50
BNO055_SIC_MATRIX_7_LSB_ADDR         = 0X51
BNO055_SIC_MATRIX_7_MSB_ADDR         = 0X52
BNO055_SIC_MATRIX_8_LSB_ADDR         = 0X53
BNO055_SIC_MATRIX_8_MSB_ADDR         = 0X54

# Accelerometer Offset registers
ACCEL_OFFSET_X_LSB_ADDR              = 0X55
ACCEL_OFFSET_X_MSB_ADDR              = 0X56
ACCEL_OFFSET_Y_LSB_ADDR              = 0X57
ACCEL_OFFSET_Y_MSB_ADDR              = 0X58
ACCEL_OFFSET_Z_LSB_ADDR              = 0X59
ACCEL_OFFSET_Z_MSB_ADDR              = 0X5A

# Magnetometer Offset registers
MAG_OFFSET_X_LSB_ADDR                = 0X5B
MAG_OFFSET_X_MSB_ADDR                = 0X5C
MAG_OFFSET_Y_LSB_ADDR                = 0X5D
MAG_OFFSET_Y_MSB_ADDR                = 0X5E
MAG_OFFSET_Z_LSB_ADDR                = 0X5F
MAG_OFFSET_Z_MSB_ADDR                = 0X60

# Gyroscope Offset register s
GYRO_OFFSET_X_LSB_ADDR               = 0X61
GYRO_OFFSET_X_MSB_ADDR               = 0X62
GYRO_OFFSET_Y_LSB_ADDR               = 0X63
GYRO_OFFSET_Y_MSB_ADDR               = 0X64
GYRO_OFFSET_Z_LSB_ADDR               = 0X65
GYRO_OFFSET_Z_MSB_ADDR               = 0X66

# Radius registers
ACCEL_RADIUS_LSB_ADDR                = 0X67
ACCEL_RADIUS_MSB_ADDR                = 0X68
MAG_RADIUS_LSB_ADDR                  = 0X69
MAG_RADIUS_MSB_ADDR                  = 0X6A

# Power modes
POWER_MODE_NORMAL                    = 0X00
POWER_MODE_LOWPOWER                  = 0X01
POWER_MODE_SUSPEND                   = 0X02

# Operation mode settings
OPERATION_MODE_CONFIG                = 0X00
OPERATION_MODE_ACCONLY               = 0X01
OPERATION_MODE_MAGONLY               = 0X02
OPERATION_MODE_GYRONLY               = 0X03
OPERATION_MODE_ACCMAG                = 0X04
OPERATION_MODE_ACCGYRO               = 0X05
OPERATION_MODE_MAGGYRO               = 0X06
OPERATION_MODE_AMG                   = 0X07
OPERATION_MODE_IMUPLUS               = 0X08
OPERATION_MODE_COMPASS               = 0X09
OPERATION_MODE_M4G                   = 0X0A
OPERATION_MODE_NDOF_FMC_OFF          = 0X0B
OPERATION_MODE_NDOF                  = 0X0C



class BNO055(object):
    def __init__(self, rst=None, address=BNO055_ADDRESS_A, i2c_bus=1, serial_port=None, serial_timeout_sec=5, logger=None):
        """BNO055のセットアップ"""

        # もしloggerが渡されなかったら，ログの記録先を標準出力に設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)
        self._logger = logger

        self.pi = pigpio.pi()  # pigpioでI2Cを扱う
        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon")
        
        # リセットピンの設定(もし使うなら)
        self._rst = rst
        if self._rst is not None:
            self.pi.set_mode(self._rst, pigpio.OUTPUT)
            self.pi.write(self._rst, 1)  # Highにしておく．LowになったらBNO055がリセットされる
            time.sleep(0.65)
            
        self._serial = None
        self._i2c_handle = None
        
        if serial_port is not None:
            """I2CではなくUARTを使う場合のピンのセットアップ"""
            # self._serial = serial.Serial(serial_port, 115200, timeout=serial_timeout_sec,
            #                            writeTimeout=serial_timeout_sec)
        else:
            """I2Cを使う場合のピンのセットアップ"""
            try:
                self._i2c_handle = self.pi.i2c_open(i2c_bus, address)
            except:
                self.pi.stop()
                raise RuntimeError("Failed to open I2C device")

    def _serial_send(self, command, ack=True, max_attempts=5):
        """UARTを使ってデータを送受信  I2Cを使用する場合は使わない"""
        # # Send a serial command and automatically handle if it needs to be resent
        # # because of a bus error.  If ack is True then an ackowledgement is
        # # expected and only up to the maximum specified attempts will be made
        # # to get a good acknowledgement (default is 5).  If ack is False then
        # # no acknowledgement is expected (like when resetting the device).
        # attempts = 0
        # while True:
        #     # Flush any pending received data to get into a clean state.
        #     self._serial.flushInput()
        #     # Send the data.
        #     self._serial.write(command)
        #     self._logger.debug('Serial send: 0x{0}'.format(binascii.hexlify(command)))
        #     # Stop if no acknowledgment is expected.
        #     if not ack:
        #         return
        #     # Read acknowledgement response (2 bytes).
        #     resp = bytearray(self._serial.read(2))
        #     self._logger.debug('Serial receive: 0x{0}'.format(binascii.hexlify(resp)))
        #     if resp is None or len(resp) != 2:
        #         raise RuntimeError('Timeout waiting for serial acknowledge, is the BNO055 connected?')
        #     # Stop if there's no bus error (0xEE07 response) and return response bytes.
        #     if not (resp[0] == 0xEE and resp[1] == 0x07):
        #         return resp
        #     # Else there was a bus error so resend, as recommended in UART app
        #     # note at:
        #     #   http://ae-bst.resource.bosch.com/media/products/dokumente/bno055/BST-BNO055-AN012-00.pdf
        #     attempts += 1
        #     if attempts >=  max_attempts:
        #         raise RuntimeError('Exceeded maximum attempts to acknowledge serial command without bus error!')

    def _write_bytes(self, address, data, ack=True):
        """I2Cでセンサの特定のレジスタアドレスに複数バイトのデータを書き込み"""
        if self._i2c_handle is not None:
            """pigpioを使ってI2Cで書き込み"""
            try:
                # I2Cでレジスタアドレス(センサ内のメモリの番地)とデータを合わせて送ることでデータを書き込む
                buffer = bytearray([address & 0xFF]) + bytearray(data)
                self.pi.i2c_write_device(self._i2c_handle, buffer)
            except:
                raise RuntimeError('I2C write error')
        else:
            """UARTを使ってデータを書き込み"""
            # command = bytearray(4+len(data))
            # command[0] = 0xAA
            # command[1] = 0x00
            # command[2] = address & 0xFF
            # command[3] = len(data) & 0xFF
            # command[4:] = map(lambda x: x & 0xFF, data)
            # resp = self._serial_send(command, ack=ack)
            # if resp[0] != 0xEE and resp[1] != 0x01:
            #     raise RuntimeError('Register write error: 0x{0}'.format(binascii.hexlify(resp)))
            
    def _write_byte(self, address, value, ack=True):
        """I2Cでセンサの特定のレジスタアドレスに1バイトのデータを書き込み"""
        if self._i2c_handle is not None:
            """pigpioを使ってI2Cで書き込み"""
            try:
                # I2Cでレジスタアドレス(センサ内のメモリの番地)とデータを合わせて送ることでデータを書き込む
                buffer = bytearray([address & 0xFF, value & 0xFF])
                self.pi.i2c_write_device(self._i2c_handle, buffer)
            except:
                raise RuntimeError('I2C write error')
        else:
            """UARTを使ってデータを書き込み"""
            # command = bytearray(5)
            # command[0] = 0xAA  # Start byte
            # command[1] = 0x00  # Write
            # command[2] = address & 0xFF
            # command[3] = 1     # Length (1 byte)
            # command[4] = value & 0xFF
            # resp = self._serial_send(command, ack=ack)
            # # Verify register write succeeded if there was an acknowledgement.
            # if ack and resp[0] != 0xEE and resp[1] != 0x01:
            #     raise RuntimeError('Register write error: 0x{0}'.format(binascii.hexlify(resp)))

    def _read_bytes(self, address, length):
        """I2Cでセンサの特定のレジスタアドレスから複数バイトのデータを読み込み"""
        if self._i2c_handle is not None:
            """pigpioを使ってI2Cで読み込み"""
            try:
                # 最初にレジスタアドレス(センサのメモリ内の番地)を送信
                self.pi.i2c_write_device(self._i2c_handle, [address & 0xFF])
                # そして，返信されてくるデータを読み込む
                count, data = self.pi.i2c_read_device(self._i2c_handle, length)
                if count != length:
                    raise RuntimeError('I2C read error')
                return bytearray(data)
            except:
                raise RuntimeError('I2C read error')
        else:
            """UARTを使ってデータを読み込み"""
            # command = bytearray(4)
            # command[0] = 0xAA
            # command[1] = 0x01
            # command[2] = address & 0xFF
            # command[3] = length & 0xFF
            # resp = self._serial_send(command)
            # if resp[0] != 0xBB:
            #     raise RuntimeError('Register read error: 0x{0}'.format(binascii.hexlify(resp)))
            # length = resp[1]
            # resp = bytearray(self._serial.read(length))
            # if resp is None or len(resp) != length:
            #     raise RuntimeError('Timeout waiting to read data, is the BNO055 connected?')
            # return resp

    def _read_byte(self, address):
        """I2Cでセンサの特定のレジスタアドレスから1バイトのデータを読み込み"""
        if self._i2c_handle is not None:
            """pigpioを使ってI2Cで読み込み"""
            try:
                # 最初にレジスタアドレス(センサのメモリ内の番地)を送信
                self.pi.i2c_write_device(self._i2c_handle, [address & 0xFF])
                # そして，返信されてくるデータを読み込む
                count, data = self.pi.i2c_read_device(self._i2c_handle, 1)
                if count != 1:
                    raise RuntimeError('I2C read error')
                return data[0]
            except:
                raise RuntimeError('I2C read error')
        else:
            """UARTを使ってデータを読み込み"""
            # return self._read_bytes(address, 1)[0]
        
    def __del__(self):
        """オブジェクトが削除されたときのクリーンアップ"""
        if self._i2c_handle is not None:
            self.pi.i2c_close(self._i2c_handle)
        if hasattr(self, 'pi'):
            self.pi.stop()

    def _read_signed_byte(self, address):
        """1バイトの符号付整数の受信"""
        data = self._read_byte(address)
        if data > 127:
            return data - 256
        else:
            return data

    def _config_mode(self):
        """configurationモードに移行"""
        self.set_mode(OPERATION_MODE_CONFIG)

    def _operation_mode(self):
        """operationモードに移行  センサの値を読み取れるようになる"""
        self.set_mode(self._mode)

    def begin(self, mode=OPERATION_MODE_NDOF):
        """BNO055を初期化する

        他のBNO055の関数を呼び出す前にこの関数を1度だけ呼び出す必要がある
        正常に初期化できたらTrue, できなかったらFalseを返す
        """
        # Save the desired normal operation mode.
        self._mode = mode
        # First send a thow-away command and ignore any response or I2C errors
        # just to make sure the BNO is in a good state and ready to accept
        # commands (this seems to be necessary after a hard power down).
        try:
            self._write_byte(BNO055_PAGE_ID_ADDR, 0, ack=False)
        except IOError:
            # Swallow an IOError that might be raised by an I2C issue.  Only do
            # this for this very first command to help get the BNO and board's
            # I2C into a clear state ready to accept the next commands.
            pass
        # Make sure we're in config mode and on page 0.
        self._config_mode()
        self._write_byte(BNO055_PAGE_ID_ADDR, 0)
        # Check the chip ID
        bno_id = self._read_byte(BNO055_CHIP_ID_ADDR)
        self._logger.debug('Read chip ID: 0x{0:02X}'.format(bno_id))
        if bno_id != BNO055_ID:
            return False
        # Reset the device.
        if self._rst is not None:
            # Use the hardware reset pin if provided.
            # Go low for a short period, then high to signal a reset.
            # self._gpio.set_low(self._rst)
            time.sleep(0.01)  # 10ms
            # self._gpio.set_high(self._rst)
        else:
            # Else use the reset command.  Note that ack=False is sent because
            # the chip doesn't seem to ack a reset in serial mode (by design?).
            self._write_byte(BNO055_SYS_TRIGGER_ADDR, 0x20, ack=False)
        # Wait 650ms after reset for chip to be ready (as suggested
        # in datasheet).
        time.sleep(0.65)
        # Set to normal power mode.
        self._write_byte(BNO055_PWR_MODE_ADDR, POWER_MODE_NORMAL)
        # Default to internal oscillator.
        self._write_byte(BNO055_SYS_TRIGGER_ADDR, 0x0)
        # Enter normal operation mode.
        self._operation_mode()
        return True

    def set_mode(self, mode):
        """Set operation mode for BNO055 sensor.  Mode should be a value from
        table 3-3 and 3-5 of the datasheet:
          http://www.adafruit.com/datasheets/BST_BNO055_DS000_12.pdf
        """
        self._write_byte(BNO055_OPR_MODE_ADDR, mode & 0xFF)
        # Delay for 30 milliseconds (datsheet recommends 19ms, but a little more
        # can't hurt and the kernel is going to spend some unknown amount of time
        # too).
        time.sleep(0.03)

    def get_revision(self):
        """Return a tuple with revision information about the BNO055 chip.  Will
        return 5 values:
          - Software revision
          - Bootloader version
          - Accelerometer ID
          - Magnetometer ID
          - Gyro ID
        """
        # Read revision values.
        accel = self._read_byte(BNO055_ACCEL_REV_ID_ADDR)
        mag = self._read_byte(BNO055_MAG_REV_ID_ADDR)
        gyro = self._read_byte(BNO055_GYRO_REV_ID_ADDR)
        bl = self._read_byte(BNO055_BL_REV_ID_ADDR)
        sw_lsb = self._read_byte(BNO055_SW_REV_ID_LSB_ADDR)
        sw_msb = self._read_byte(BNO055_SW_REV_ID_MSB_ADDR)
        sw = ((sw_msb << 8) | sw_lsb) & 0xFFFF
        # Return the results as a tuple of all 5 values.
        return (sw, bl, accel, mag, gyro)

    def set_external_crystal(self, external_crystal):
        """Set if an external crystal is being used by passing True, otherwise
        use the internal oscillator by passing False (the default behavior).
        """
        # Switch to configuration mode.
        self._config_mode()
        # Set the clock bit appropriately in the SYS_TRIGGER register.
        if external_crystal:
            self._write_byte(BNO055_SYS_TRIGGER_ADDR, 0x80)
        else:
            self._write_byte(BNO055_SYS_TRIGGER_ADDR, 0x00)
        # Go back to normal operation mode.
        self._operation_mode()

    def get_system_status(self, run_self_test=True):
        """Return a tuple with status information.  Three values will be returned:
          - System status register value with the following meaning:
              0 = Idle
              1 = System Error
              2 = Initializing Peripherals
              3 = System Initialization
              4 = Executing Self-Test
              5 = Sensor fusion algorithm running
              6 = System running without fusion algorithms
          - Self test result register value with the following meaning:
              Bit value: 1 = test passed, 0 = test failed
              Bit 0 = Accelerometer self test
              Bit 1 = Magnetometer self test
              Bit 2 = Gyroscope self test
              Bit 3 = MCU self test
              Value of 0x0F = all good!
          - System error register value with the following meaning:
              0 = No error
              1 = Peripheral initialization error
              2 = System initialization error
              3 = Self test result failed
              4 = Register map value out of range
              5 = Register map address out of range
              6 = Register map write error
              7 = BNO low power mode not available for selected operation mode
              8 = Accelerometer power mode not available
              9 = Fusion algorithm configuration error
             10 = Sensor configuration error

        If run_self_test is passed in as False then no self test is performed and
        None will be returned for the self test result.  Note that running a
        self test requires going into config mode which will stop the fusion
        engine from running.
        """
        self_test = None
        if run_self_test:
            # Switch to configuration mode if running self test.
            self._config_mode()
            # Perform a self test.
            sys_trigger = self._read_byte(BNO055_SYS_TRIGGER_ADDR)
            self._write_byte(BNO055_SYS_TRIGGER_ADDR, sys_trigger | 0x1)
            # Wait for self test to finish.
            time.sleep(0.1)
            # Read test result.
            self_test = self._read_byte(BNO055_SELFTEST_RESULT_ADDR)
            # Go back to operation mode.
            self._operation_mode()
        # Now read status and error registers.
        status = self._read_byte(BNO055_SYS_STAT_ADDR)
        error = self._read_byte(BNO055_SYS_ERR_ADDR)
        # Return the results as a tuple of all 3 values.
        return (status, self_test, error)

    def get_calibration_status(self):
        """Read the calibration status of the sensors and return a 4 tuple with
        calibration status as follows:
          - System, 3=fully calibrated, 0=not calibrated
          - Gyroscope, 3=fully calibrated, 0=not calibrated
          - Accelerometer, 3=fully calibrated, 0=not calibrated
          - Magnetometer, 3=fully calibrated, 0=not calibrated
        """
        # Return the calibration status register value.
        cal_status = self._read_byte(BNO055_CALIB_STAT_ADDR)
        sys = (cal_status >> 6) & 0x03
        gyro = (cal_status >> 4) & 0x03
        accel = (cal_status >> 2) & 0x03
        mag = cal_status & 0x03
        # Return the results as a tuple of all 3 values.
        return (sys, gyro, accel, mag)

    def get_calibration(self):
        """Return the sensor's calibration data and return it as an array of
        22 bytes. Can be saved and then reloaded with the set_calibration function
        to quickly calibrate from a previously calculated set of calibration data.
        """
        # Switch to configuration mode, as mentioned in section 3.10.4 of datasheet.
        self._config_mode()
        # Read the 22 bytes of calibration data and convert it to a list (from
        # a bytearray) so it's more easily serialized should the caller want to
        # store it.
        cal_data = list(self._read_bytes(ACCEL_OFFSET_X_LSB_ADDR, 22))
        # Go back to normal operation mode.
        self._operation_mode()
        return cal_data

    def set_calibration(self, data):
        """Set the sensor's calibration data using a list of 22 bytes that
        represent the sensor offsets and calibration data.  This data should be
        a value that was previously retrieved with get_calibration (and then
        perhaps persisted to disk or other location until needed again).
        """
        # Check that 22 bytes were passed in with calibration data.
        if data is None or len(data) != 22:
            raise ValueError('Expected a list of 22 bytes for calibration data.')
        # Switch to configuration mode, as mentioned in section 3.10.4 of datasheet.
        self._config_mode()
        # Set the 22 bytes of calibration data.
        self._write_bytes(ACCEL_OFFSET_X_LSB_ADDR, data)
        # Go back to normal operation mode.
        self._operation_mode()

    def get_axis_remap(self):
        """Return a tuple with the axis remap register values.  This will return
        6 values with the following meaning:
          - X axis remap (a value of AXIS_REMAP_X, AXIS_REMAP_Y, or AXIS_REMAP_Z.
                          which indicates that the physical X axis of the chip
                          is remapped to a different axis)
          - Y axis remap (see above)
          - Z axis remap (see above)
          - X axis sign (a value of AXIS_REMAP_POSITIVE or AXIS_REMAP_NEGATIVE
                         which indicates if the X axis values should be positive/
                         normal or negative/inverted.  The default is positive.)
          - Y axis sign (see above)
          - Z axis sign (see above)

        Note that by default the axis orientation of the BNO chip looks like
        the following (taken from section 3.4, page 24 of the datasheet).  Notice
        the dot in the corner that corresponds to the dot on the BNO chip:

                           | Z axis
                           |
                           |   / X axis
                       ____|__/____
          Y axis     / *   | /    /|
          _________ /______|/    //
                   /___________ //
                  |____________|/
        """
        # Get the axis remap register value.
        map_config = self._read_byte(BNO055_AXIS_MAP_CONFIG_ADDR)
        z = (map_config >> 4) & 0x03
        y = (map_config >> 2) & 0x03
        x = map_config & 0x03
        # Get the axis remap sign register value.
        sign_config = self._read_byte(BNO055_AXIS_MAP_SIGN_ADDR)
        x_sign = (sign_config >> 2) & 0x01
        y_sign = (sign_config >> 1) & 0x01
        z_sign = sign_config & 0x01
        # Return the results as a tuple of all 3 values.
        return (x, y, z, x_sign, y_sign, z_sign)

    def set_axis_remap(self, x, y, z,
                       x_sign=AXIS_REMAP_POSITIVE, y_sign=AXIS_REMAP_POSITIVE,
                       z_sign=AXIS_REMAP_POSITIVE):
        """Set axis remap for each axis.  The x, y, z parameter values should
        be set to one of AXIS_REMAP_X, AXIS_REMAP_Y, or AXIS_REMAP_Z and will
        change the BNO's axis to represent another axis.  Note that two axises
        cannot be mapped to the same axis, so the x, y, z params should be a
        unique combination of AXIS_REMAP_X, AXIS_REMAP_Y, AXIS_REMAP_Z values.

        The x_sign, y_sign, z_sign values represent if the axis should be positive
        or negative (inverted).

        See the get_axis_remap documentation for information on the orientation
        of the axises on the chip, and consult section 3.4 of the datasheet.
        """
        # Switch to configuration mode.
        self._config_mode()
        # Set the axis remap register value.
        map_config = 0x00
        map_config |= (z & 0x03) << 4
        map_config |= (y & 0x03) << 2
        map_config |= x & 0x03
        self._write_byte(BNO055_AXIS_MAP_CONFIG_ADDR, map_config)
        # Set the axis remap sign register value.
        sign_config = 0x00
        sign_config |= (x_sign & 0x01) << 2
        sign_config |= (y_sign & 0x01) << 1
        sign_config |= z_sign & 0x01
        self._write_byte(BNO055_AXIS_MAP_SIGN_ADDR, sign_config)
        # Go back to normal operation mode.
        self._operation_mode()

    def _read_vector(self, address, count=3):
        # Read count number of 16-bit signed values starting from the provided
        # address. Returns a tuple of the values that were read.
        data = self._read_bytes(address, count*2)
        result = [0]*count
        for i in range(count):
            result[i] = ((data[i*2+1] << 8) | data[i*2]) & 0xFFFF
            if result[i] > 32767:
                result[i] -= 65536
        return result

    def read_euler(self):
        try:
            """Return the current absolute orientation as a tuple of heading, roll,
            and pitch euler angles in degrees.
            """
            heading, roll, pitch = self._read_vector(BNO055_EULER_H_LSB_ADDR)
            self._logger.debug(f"euler: {heading/16.0}, {roll/16.0}, {pitch/16.0}")
            return (heading/16.0, roll/16.0, pitch/16.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading euler")

    def read_magnetometer(self):
        try:
            """Return the current magnetometer reading as a tuple of X, Y, Z values
            in micro-Teslas.
            """
            x, y, z = self._read_vector(BNO055_MAG_DATA_X_LSB_ADDR)
            self._logger.debug(f"mag: {x/16.0}, {y/16.0}, {z/16.0}")
            return (x/16.0, y/16.0, z/16.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading magnetometer")

    def read_gyroscope(self):
        try:
            """Return the current gyroscope (angular velocity) reading as a tuple of
            X, Y, Z values in degrees per second.
            """
            x, y, z = self._read_vector(BNO055_GYRO_DATA_X_LSB_ADDR)
            self._logger.debug(f"gyro: {x/900.0}, {y/900.0}, {z/900.0}")
            return (x/900.0, y/900.0, z/900.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading gyroscope")

    def read_accelerometer(self):
        try:
            """Return the current accelerometer reading as a tuple of X, Y, Z values
            in meters/second^2.
            """
            x, y, z = self._read_vector(BNO055_ACCEL_DATA_X_LSB_ADDR)
            self._logger.debug(f"accel: {x/100.0}, {y/100.0}, {z/100.0}")
            return (x/100.0, y/100.0, z/100.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading accelerometer")

    def read_linear_acceleration(self):
        try:
            """Return the current linear acceleration (acceleration from movement,
            not from gravity) reading as a tuple of X, Y, Z values in meters/second^2.
            """
            x, y, z = self._read_vector(BNO055_LINEAR_ACCEL_DATA_X_LSB_ADDR)
            self._logger.debug(f"liner_accel: {x/100.0}, {y/100.0}, {z/100.0}")
            return (x/100.0, y/100.0, z/100.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading linear acceleration")

    def read_gravity(self):
        try:
            """Return the current gravity acceleration reading as a tuple of X, Y, Z
            values in meters/second^2.
            """
            x, y, z = self._read_vector(BNO055_GRAVITY_DATA_X_LSB_ADDR)
            self._logger.debug(f"grav: {x/100.0}, {y/100.0}, {z/100.0}")
            return (x/100.0, y/100.0, z/100.0)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading gravity")

    def read_quaternion(self):
        try:
            """Return the current orientation as a tuple of X, Y, Z, W quaternion
            values.
            """
            w, x, y, z = self._read_vector(BNO055_QUATERNION_DATA_W_LSB_ADDR, 4)
            # Scale values, see 3.6.5.5 in the datasheet.
            scale = (1.0 / (1<<14))
            self._logger.debug(f"quaternion: {x*scale}, {y*scale}, {z*scale}")
            return (x*scale, y*scale, z*scale, w*scale)
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading quaternion")

    def read_temp(self):
        try:
            """Return the current temperature in Celsius."""
            temperature = self._read_signed_byte(BNO055_TEMP_ADDR)
            self._logger.debug(f"bno_temp: {temperature}")
            return temperature
        except Exception as e:
            self._logger.exception("An error occured in bno055 reading temperture")
    
    # ずっと測定し続ける
    def get_forever(self, data):
        while True:
            try:
                # self.read_euler()
                data["mag"][0], data["mag"][1], data["mag"][2] = self.read_magnetometer()
                data["gyro"][0], data["gyro"][1], data["gyro"][2] = self.read_gyroscope()
                data["accel"][0], data["accel"][1], data["accel"][2] = self.read_accelerometer()
                data["line_accel"][0], data["line_accel"][1], data["line_accel"][2] = self.read_linear_acceleration()
                data["grav"][0], data["grav"][1], data["grav"][2] = self.read_gravity()
                # self.read_quaternion()
                # self.read_temp()
                # calc_goal.calc_goal(data)  # ゴールまでの距離と向きを計算
                time.sleep(0.2)
            except Exception as e:
                self._logger.exception(f"An error occured in bno055 get_forever: {e}")

if __name__ == "__main__":
    try:
        # データ取得のサンプル

        # Create and configure the BNO sensor connection.  Make sure only ONE of the
        # below 'bno = ...' lines is uncommented:
        # Raspberry Pi configuration with serial UART and RST connected to GPIO 18:
        bno = BNO055(address=BNO055_ADDRESS_B)
        # BeagleBone Black configuration with default I2C connection (SCL=P9_19, SDA=P9_20),
        # and RST connected to pin P9_12:
        #bno = BNO055.BNO055(rst='P9_12')


        # Enable verbose debug logging if -v is passed as a parameter.
        # if len(sys.argv) == 2 and sys.argv[1].lower() == '-v':
        #     logging.basicConfig(level=logging.DEBUG)

        # Initialize the BNO055 and stop if something went wrong.
        if not bno.begin():
            raise RuntimeError('Failed to initialize BNO055! Is the sensor connected?')

        # Print system status and self test result.
        status, self_test, error = bno.get_system_status()
        print('System status: {0}'.format(status))
        print('Self test result (0x0F is normal): 0x{0:02X}'.format(self_test))
        # Print out an error if system status is in error mode.
        if status == 0x01:
            print('System error: {0}'.format(error))
            print('See datasheet section 4.3.59 for the meaning.')

        # Print BNO055 software revision and other diagnostic data.
        sw, bl, accel, mag, gyro = bno.get_revision()
        print('Software version:   {0}'.format(sw))
        print('Bootloader version: {0}'.format(bl))
        print('Accelerometer ID:   0x{0:02X}'.format(accel))
        print('Magnetometer ID:    0x{0:02X}'.format(mag))
        print('Gyroscope ID:       0x{0:02X}\n'.format(gyro))

        print('Reading BNO055 data, press Ctrl-C to quit...')
        while True:

            # キャリブレーションの状態(これは測定値ではない！), 0=uncalibrated and 3=fully calibrated.
            _sys, gyro, accel, mag = bno.get_calibration_status()
            # Print everything out.
            print('Gyro_cal={0} Accel_cal={1} Mag_cal={2}'.format(gyro, accel, mag))

            # Other values you can optionally read:
            
            # 4元数方位
            # Orientation as a quaternion:
            #x,y,z,w = bno.read_quaterion()
            
            # 温度(℃)
            # temp_c = bno.read_temp()

            # オイラー角(deg)
            # heading, roll, pitch = bno.read_euler()

            # 地磁気(μT)
            mag_x,mag_y,mag_z = bno.read_magnetometer()
            
            # ジャイロ(deg/s)
            gyro_x,gyro_y,gyro_z = bno.read_gyroscope()

            # 加速度(m s^-2)
            # Accelerometer data (in meters per second squared):
            # x,y,z = bno.read_accelerometer()

            # 線形加速度(m s^-2)  (全加速度から重力加速度を取り除いたもの)
            # returned in meters per second squared):
            liner_accel_x,liner_accel_y,liner_accel_z = bno.read_linear_acceleration()

            # 重力加速度(m s^-2)
            gravity_x,gravity_y,gravity_z = bno.read_gravity()

            print(f"magnetometer: \nmag_x:{mag_x:.4f}  mag_y:{mag_y:.4f}  mag_z:{mag_z:.4f}")
            print(f"gyroscope: \ngyro_x:{gyro_x:.4f}  gyro_y:{gyro_y:.4f}  mag_z:{gyro_z:.4f}")
            print(f"liner_accel: \nliner_accel_x:{liner_accel_x:.4f}  liner_accel_y:{liner_accel_y:.4f}  liner_accel_z:{liner_accel_z:.4f}")
            print(f"gravity: \ngravity_x:{gravity_x:.4f}  gravity_y:{gravity_y:.4f}  gravity_z:{gravity_z:.4f}")
            print()

            time.sleep(1)

    except Exception as e:
        print(f"An error occured in BNO055: {e}")