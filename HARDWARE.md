# Tested FM4 hardware

Pi 4B, aarch64 piCorePlayer 11.1.0; 256×64 SSD1322 OLED on SPI0 CE0.

| Function | BCM GPIO / bus |
| --- | --- |
| OLED DC / reset | 24 / 25 |
| Rotary encoder A / B / switch | 13 / 5 / 6 |
| Buttons and LEDs | MCP23017, I2C-1 address 0x20 |
| Shutdown switch | 21 |
| IR receiver, verified on this unit | **4**, physical pin 7 |

The IR pin differs from the previously assumed GPIO27. GPIO4 was verified by
captured pulses and the user confirmed Apple remote operation. Use Settings →
Pair Apple Remote to learn its identity. Pi headphones and the SMSL USB DAC are
available through Settings → Audio Output. Native SPI/I2C must be enabled before
installing. See the original [Quadify wiring](https://quadify.uk/wiring.html),
with this unit's verified IR exception above.
