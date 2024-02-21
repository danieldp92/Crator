import os
from pathlib import Path

resource_path = Path(__file__).parent.parent.parent.joinpath("resources")


def get_seeds():
    seeds_path = os.path.join(resource_path, 'seeds.txt')
    with open(seeds_path, 'r') as file:
        seeds = file.readlines()
        seeds = [seed.strip() for seed in seeds]

    return seeds