1. **Import `asyncio`**: Add `import asyncio` to `all_in_one_bridge.py`.
2. **Make `generate_image` asynchronous**: Change `def generate_image` to `async def generate_image`. Replace all `time.sleep()` calls inside `generate_image` with `await asyncio.sleep()`. This includes `time.sleep(1800)`, `time.sleep(pre_delay)`, and `time.sleep(wait_secs)`.
3. **Update calls to `generate_image`**: Inside `all_in_one_bridge.py` (`do_POST`), update the call to `generate_image` by wrapping it in `asyncio.run()`, i.e., `asyncio.run(generate_image(...))`.
4. **Complete pre-commit steps**: Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
5. **Submit the PR**: Submit the PR with the performance optimization and required details in the description.
