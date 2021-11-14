# Aguitare Project V.1.0

This project aims to 'replace' the right hand of the guitarist, to allow him to play a second instrument simultaneously.


## Software
### Installation

The only library on which the project relies on is the **pyguitarpro** lib, which allows to parse tab files.
You can directly install it through **pip**:

```bash
pip3 install PyGuitarPro
```

## Hardware

### Material
* Rapsberry 3B +
* Adafruit PWM 16 channel PCA9685
* LCD with I2C communication
* 6 x 9G servo motors
* A bunch of push buttons (4 for navigating the menu, and 6 to trigger the servos)
* A 5V battery (With 3A max output in my case)

### Scheme



## Usage

```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)