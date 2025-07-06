import time

from llms.llm_cache import LLMCache

if __name__ == "__main__":
    import argparse
    import os
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Remove a model from the cache.")
    parser.add_argument(
        "model_name", type=str, help="Name of the model to remove from the cache.")
    parser.add_argument(
        "cache",
        type=str,
        default="/tmp/llm_cache",
        help="Cache file"
    )
    args = parser.parse_args()

    # Create backup of the cache
    current_time = time.strftime("%Y%m%d-%H%M%S")
    backup_path = args.cache + f"_{current_time}_backup"
    cache = LLMCache(args.cache)
    print(f"Found {len(cache.entries)} entries in cache.")
    print(f"Backing up cache from {args.cache} to {backup_path}")
    os.rename(args.cache, backup_path)
    new_cache = LLMCache(args.cache)
    models_in_cache = set(entry['model'] for entry in cache.entries)
    print(f"Models in cache: {', '.join(models_in_cache)}")
    for entry in cache.entries:
        if entry['model'] != args.model_name:
            new_cache.add(
                prompt=str(entry['prompt']),
                model=str(entry['model']),
                seed=int(entry['seed']),
                temperature=float(entry['temperature']),
                response=str(entry['response'])
            )
    print(f"Removed {len(cache.entries) - len(new_cache.entries)} entries for model {args.model_name}.")
    print(f"New cache has {len(new_cache.entries)} entries.")
