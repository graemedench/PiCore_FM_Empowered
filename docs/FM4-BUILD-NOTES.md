# FM4 build notes

## Front-panel IR conversion

The original **LED 8** position is reused as the visible opening for the
HS0038 IR receiver.

- LED 8 is **not disconnected**: its MCP23017 connection remains intact.
- The LED itself is pulled back behind the front panel so it does not occupy
  the opening or shine directly through the receiver position.
- The HS0038 receiver is mounted in the old LED-8 opening, with its OUT pin on
  Raspberry Pi GPIO4 (physical pin 7), VCC on 3.3 V and GND on ground.

This keeps the eight-channel LED hardware reversible while giving the IR sensor
a neat, front-facing location.

## Rear Ethernet jack conversion

[`Rear Network Jack`](../FM4%20Mounting%20Parts/Rear%20Network%20Jack/) holds a
panel-mount Ethernet extension in the original rear IEC / **POWER OUT** opening.
It uses the original opening and fixing points, so no drilling or cutting is
required.

With the unit disconnected from mains power, have any original mains wiring
made safe by a suitably competent person before removing the original IEC
hardware. Retain the original outlet/inlet hardware and screws if the FM4 may
later be returned to its original condition.

## Included mounting parts

The current printable mounting parts are in
[`FM4 Mounting Parts`](../FM4%20Mounting%20Parts/): screen holder, rotary-knob
bracket, knob extender and the rear Ethernet-jack panel.

## piCorePlayer port notes

Copied from Quadify Empowered and adapted for this unit. The IR signal pin was
verified as GPIO4 during the piCorePlayer port. See [HARDWARE.md](../HARDWARE.md)
and the [updated wiring diagram](FM4-WIRING-DIAGRAM.svg). The remaining printed
mounting parts retain their original versions. Additional editable CAD, USB
rear-panel parts and the PCB test template are under
[Hardware Design Sources](../Hardware%20Design%20Sources/README.md). Those are
working designs rather than a claim of tested fit.
