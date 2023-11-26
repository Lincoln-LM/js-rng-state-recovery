# js-rng-state-recovery
Recovery of the internal Xorshift128+ state based on 64/128 consecutive outputs of ``Math.random()`` on V8 and SpiderMonkey via Linear Algebra

## Usage
### Requires Python 3.12+

```bash
usage: main.py [-h] [--js-engine JS_ENGINE] [--website WEBSITE] [--amount AMOUNT] [--json-path JSON_PATH]

options:
  -h, --help            show this help message and exit
  --js-engine JS_ENGINE
                        JavaScript engine (v8, spidermonkey)
  --website WEBSITE     Coin flip website (probable, google)
  --amount AMOUNT       Amount of coin flips to predict
  --json-path JSON_PATH
                        Path to json containing the Math.random() outputs
```

Open the JavaScript console and record 64 (V8) or 128 (SpiderMonkey) ``Math.random()`` outputs by running ``Array.from(Array(64), Math.random)`` or ``Array.from(Array(128), Math.random)``

Right click, copy the object, and paste it into ``observations.json`` or some other specified json path prior to running the program

### Examples
Predict 5 coin flips from the google-integrated coin flip on Google Chrome (V8)

``python main.py --js-engine=v8 --website=google --amount=5``

Predict 15 coin flips from [Probable](https://edjefferson.com/probable/) on FireFox (SpiderMonkey)

``python main.py --js-engine=spidermonkey --website=probable --amount=15``