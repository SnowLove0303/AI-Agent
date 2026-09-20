# Design Document: Section 2 Semantic Completion & Jev Intelligent Routing Engine

## Architecture
1. Semantic Precautionary & Hazard Code Completion:
   - scripts/ghs_code_resolver.py: Built-in deterministic dictionary mapping standard Chinese and English precautionary text fragments to GHS codes.
   - When raw source lacks alphanumeric P-codes, resolver detects phrases (e.g. 穿戴必要的防护用品 -> P280, 彻底清洗 -> P264, 不得进食 -> P270, 通风良好 -> P271, 漱口、禁止催吐 -> P301+P330+P331, 密闭容器/收集 -> P391, 阴凉通风 -> P403+P235, 国家法律法规处置 -> P501).
2. Jev System One Dispatcher (scripts/jev_dispatcher.py):
   - Bridges C:\Users\Administrator\.jev\jev.py into the MSDS pipeline.
   - Fallback-safe: if Jev is unreachable or offline, defaults to deterministic regex/rule patterns.
   - Questions dispatched:
     - resolve_signal_word: extracts and normalizes 警告 / 危险 / 无信号词.
     - route_s3_exemptions: detects amine salt / neutralization / threshold statements in Section 3 and formats them for Section 2.3 label elements.
3. Section 2 Table Mutator:
   - scripts/section2_ghs_policy.py: When signal word or precautionary/hazard statements exist, preserve their dedicated rows.
   - Suppress only genuinely empty/absent rows, avoiding blanket deletion of physical/chemical hazards and precautionary groups.
4. Section 11 Multi-Tier Writer:
   - Preserves lead line: 该产品无可用的毒理学研究。
   - Preserves polymer line: 羟基聚丙烯酸酯分散体：毒性：无资料；刺激性：无资料。
   - Preserves component qualifier: 以下为组分二丙二醇丁醚（CAS 29911-28-2）的毒理学参考数据：
