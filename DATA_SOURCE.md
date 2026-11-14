# 素数数据来源

- 项目：[stdlib-js/datasets-primes-100k](https://github.com/stdlib-js/datasets-primes-100k)
- 提供方：The Stdlib Authors
- 数据：按升序排列的前 100,000 个素数，从 2 到 1,299,709
- 包版本：0.2.3
- 固定提交：`631f9044ddae1ea938c4555960ab9ac6d71635a5`
- 原始文件：[data/data.json](https://raw.githubusercontent.com/stdlib-js/datasets-primes-100k/631f9044ddae1ea938c4555960ab9ac6d71635a5/data/data.json)
- 原始文件 SHA-256：`e45f6e05dd36a8ac1f4e9e7e3928c741af275aded4b60b65d94c08c35618f608`
- 导入日期：2026-11-14

依据[该提交的许可声明](https://github.com/stdlib-js/datasets-primes-100k/blob/631f9044ddae1ea938c4555960ab9ac6d71635a5/README.md#license)，数据文件采用 [Open Data Commons Public Domain Dedication & License 1.0](https://opendatacommons.org/licenses/pddl/1-0/)，内容采用 [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)。

`generate_primes.py` 读取并校验这份 JSON，将每个素数对应的位设为 1，其他位为 0，添加查询上限文件头后得到 `primes.bin`。默认导入完整数据集；不重新计算素数。

验证使用独立的试除法，逐项检查 0 到 1,299,709，包括素数和合数，并核对素数总数为 100,000。
