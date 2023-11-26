"""Main module to be executed"""
import json
import sys
import argparse
from typing import Iterable
from core.recover_state import recover_rng
from core.xorshift import Xorshift

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--js-engine", help="JavaScript engine (v8, spidermonkey)")
arg_parser.add_argument("--website", help="Coin flip website (probable, google)")
arg_parser.add_argument(
    "--amount",
    help="Amount of coin flips to predict",
    default="15",
)
arg_parser.add_argument(
    "--json-path",
    help="Path to json containing the Math.random() outputs",
    default="observations.json",
)
args = arg_parser.parse_args()

if args.js_engine not in ("v8", "spidermonkey"):
    print(f"Error: {args.js_engine=} is an invalid value")
    arg_parser.print_help()
    sys.exit(1)
if args.website not in ("google", "probable"):
    print(f"Error: {args.website=} is an invalid value")
    arg_parser.print_help()
    sys.exit(1)
if not args.amount.isdigit():
    print(f"Error: {args.website=} is an invalid value")
    arg_parser.print_help()
    sys.exit(1)

with open(args.json_path, "r", encoding="utf-8") as observations_file:
    observations = json.load(observations_file)


def predict_probable_coin(rng: Xorshift, amount: int) -> Iterable[str]:
    """Predict the next N results of the https://edjefferson.com/probable/ coinflip"""
    for _ in range(amount):
        yield "Heads" if rng.math_random() < 0.5 else "Tails"


def predict_google_coin(rng: Xorshift, amount: int) -> Iterable[str]:
    """Predict the next N results of the https://www.google.com/search?q=coin+flip coinflip"""
    for _ in range(amount):
        yield "Heads" if rng.math_random() < 0.5 else "Tails"
        for _ in range(4):
            rng.math_random()


for rng in recover_rng(
    observations,
    v8=args.js_engine == "v8",
):
    predict_func = (
        predict_google_coin if args.website == "google" else predict_probable_coin
    )
    print(f"{rng.state[0]=:08X} {rng.state[1]=:08X}")
    for prediction in predict_func(rng, int(args.amount)):
        print(prediction)
