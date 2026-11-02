# Diagrams (v1.5): chosen by content, not by a fixed list

The export does not draw the same figures for every product. `scripts/diagram_plan.py` reads the spec, measures signals, and scores each candidate diagram **Must / Should / Could**. The profile and the per-feature budget then decide what is drawn. Diagrams that a script can draw from the spec tables are drawn automatically. Diagrams that need understanding are written by the `spec-diagrammer` agent as fenced blocks in the md files.

## Catalog and where each one goes in the SRS

| Type | SRS place | Trigger (signal) | Level | Who draws it |
|---|---|---|---|---|
| context | 1.5 (end of section 1) | ≥1 external system in config (`external_systems` or `external_actors_note`) | Must | auto (a `context` block overrides) |
| uc_overview | 2.3 | always | Must | auto |
| uc_module | 2.4.n | every module | Must | auto |
| process | 2.5.n (first) | ≥3 modules and ≥3 cross-module links | Must | **agent** (`process` / `journey` block in 0-overview.md) |
| linkmap | 2.5.n | same as process | Should | auto |
| state | 2.6 per use case | "State lifecycle" table with ≥2 transitions | Must | auto (a `state` block overrides); a repeated state set prints a reference instead |
| activity | 2.6 per use case | ≥5 main steps or ≥2 alternate flows | Must if money or ≥8 steps, else Should | auto, with branches from alternate flows |
| sequence | 2.6 per use case | a flow mentions an external system | Must if money, else Should | **agent** |
| flow (wizard) | 2.6 per use case | ≥3 numbered steps ("bước 2", "step 3") | Should | **agent** |
| decision | 2.6 per use case (table) | ≥3 business rules with combined conditions | Should | **agent** |
| timeline | 2.6 per use case | ≥2 time limits (minutes, hours, days) | Should | **agent** |
| screen_map | 3.1 | ≥5 screens in the module maps | Should | auto |
| perm_matrix | 3.2 (table) | ≥2 human roles | Should | auto |
| erd | 3.4 "Data requirements" (classic: end of 3.3) | ≥3 entities (source/content-model.md, else api.md resources) | Should | **agent** (`erd` block in 0-overview.md) |

In 2.5 the old "longest flow of each module" figure is kept only when 2.6 does not already draw that use case; otherwise 2.5 points to it, so nothing is drawn twice.

## Profiles (`config.json` → `"diagrams": {"profile": ..., "include": [...], "exclude": [...]}`)

| Profile | For | Types | Per use case |
|---|---|---|---|
| `full` (default) | SRS for PO + dev + QA | all | 3 figures |
| `classic` (default for `template: classic`) | customer template | context, UC, process, state, activity, sequence, erd, decision | 2 |
| `po` | business readers | context, UC overview, process, linkmap, state, screen map, flow, permission matrix | 1 |
| `dev` | developers | context, state, sequence, erd, decision, activity, timeline, permission matrix | 3 |

`include` / `exclude` take type names and win over the profile. Inside the budget the order is Must, then Should, then Could.

## Block syntax (fenced code inside the md files)

Put a block in the feature it belongs to (anywhere in the feature, usually after Main flow), or in `0-overview.md` for document-level types (process, context, erd). The first line is ` ```diagram <type>: <title>`. Labels are short (≤90 characters, aim for 40), in the spec language, with no personal data. A line that carries `(Unverified)`, `(PO proposal)` or `(Inferred)` is drawn dashed. Lines starting with `#` are comments. Keep each block ≤25 nodes; split bigger ones.

**process / journey / flow**: one step per line `Lane | step`; a branch after the previous step is `? condition -> Lane | what happens`.
````
```diagram process: Đặt khám từ tìm kiếm đến thanh toán
Bệnh nhân | Tìm bác sĩ hoặc cơ sở (1.2)
Bệnh nhân | Chọn ngày và khung giờ (7.1)
? Chưa đăng nhập -> Hệ thống | Mở màn đăng nhập rồi quay lại bước này
Hệ thống | Tạo lịch khám ở trạng thái Đặt lịch
Cổng thanh toán | Thu phí (7.4)
```
````

**sequence**: `A -> B: message`; `-->` is a reply or an unverified call.
````
```diagram sequence: Thanh toán qua cổng
Bệnh nhân -> Web: Bấm "Thanh toán"
Web -> API: Tạo giao dịch
API -> Cổng thanh toán: Chuyển hướng kèm mã giao dịch
Cổng thanh toán --> API: Kết quả (callback)
API --> Web: Cập nhật trạng thái lịch khám
```
````

**state**: `From -> To: who / action`; `[*]` is the start or end. Only when the State lifecycle table is not enough (several objects, nested states).

**erd**: `Entity: field, field` and `A 1--n B: label` (cardinalities 0, 1, n, *, 0..1, 1..n, 0..n). Fields are names only, no sample values.
````
```diagram erd: Dữ liệu đặt khám
Bệnh nhân: mã, họ tên, ngày sinh
Hồ sơ: mã, quan hệ
Lịch khám: mã, ngày giờ, trạng thái
Bệnh nhân 1--n Hồ sơ: sở hữu
Hồ sơ 1--n Lịch khám: đặt cho
```
````

**decision**: a markdown table, conditions as columns and the outcome last.
````
```diagram decision: Được huỷ lịch hay không
| Trạng thái | Còn trên 24 giờ | Đã thanh toán | Kết quả |
|---|---|---|---|
| Đặt lịch | Có | Không | Huỷ ngay |
| Đặt lịch | Có | Có | Huỷ và hoàn tiền |
| Đặt lịch | Không | bất kỳ | Không cho huỷ |
```
````

**timeline**: `when | what`.
````
```diagram timeline: Giữ chỗ khi đặt khám
0 phút | Giữ khung giờ
10 phút | Hết giữ chỗ nếu chưa xác nhận
24 giờ trước giờ khám | Hết hạn huỷ miễn phí
```
````

**context**: `System | what it exchanges`, one external system per line.

## Rules
- Draw only what the spec already says. A diagram never adds a fact; if a step is not in the spec, add it to the spec first with its source label.
- Every arrow label uses the exact button or status label from the spec.
- Gate: `diagram_check.py <md_dir> config.json` must have no FAIL (missing Must block, syntax error, >25 nodes). WARN rows (missing Should, long labels) are fixed when cheap, otherwise accepted.
