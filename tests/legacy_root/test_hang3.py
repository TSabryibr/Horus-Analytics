from core.exclusions import get_all_exclusions

print("calling get_all_exclusions")
exc = get_all_exclusions()
print("done! count:", len(exc))
