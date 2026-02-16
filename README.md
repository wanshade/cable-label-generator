# Cable Label Generator 🏷️⚡

Generate DXF labels for cable tagging from CSV schedule data.

## Features

- 📄 Parse CSV cable schedules
- 🏷️ Generate DXF labels with cable ID, specs, origin, destination
- 📐 Auto-arrange labels in grid layout for laser cutting
- 🔧 4 mounting holes per label (5mm from corners)
- 🎨 Layer configuration: Cutting (Cyan), Hole (Red), Text (Blue)
- 📋 Supports AutoCAD 2010+ (DXF R2010 format)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python generate_labels.py cables.csv
```

### Options

```bash
# Generate both combined sheets and individual files
python generate_labels.py cables.csv --individual

# Only generate combined sheets (default)
python generate_labels.py cables.csv

# Specify output directory
python generate_labels.py cables.csv -o ./my_labels

# Skip combined sheets, only individual
python generate_labels.py cables.csv --individual --no-combined
```

## CSV Format

The CSV should have these columns:
```csv
CABLE_ID,SPECIFICATION,ORIGIN,DESTINATION
M1D-TX-010A,500mm² 110 XLPE CU FLEX 20-OF,M1D-TX-010A,M1D-MSB-010A
M1D-MSB-010A,240mm² 110 XLPE CU FLEX 8-OF,M1D-MSB-010A,M1D-PDU-010-A1
```

Or with headers:
```csv
Cable ID,Specification,Origin,Destination
M1D-TX-010A,500mm² 110 XLPE CU FLEX 20-OF,ORIGIN: M1D-TX-010A,DESTINATION: M1D-MSB-010A
```

## Label Specifications

| Property | Value |
|----------|-------|
| Label Size | 80mm x 40mm |
| Mounting Holes | **5mm x 2.5mm** rectangular, 5mm from corners |
| Hole Spacing | 70mm x 30mm (center-to-center) |
| Sheet Layout | 6 labels per row, 7 rows = 42 labels per sheet |
| Sheet Size | ~500mm x 320mm |

## Output Structure

```
output/
├── cable_labels_sheet_01.dxf  (Combined sheet 1)
├── cable_labels_sheet_02.dxf  (Combined sheet 2)
├── cable_labels_sheet_03.dxf  (Combined sheet 3)
└── ... (individual files if --individual flag used)
```

## Layer Colors

| Layer | Color | Purpose |
|-------|-------|---------|
| Cutting | Cyan (4) | Label outline for cutting |
| Hole | Red (1) | Mounting holes |
| Text | Blue (5) | Cable information |

## Example Label Content

```
┌─────────────────────────┐ ◄── 80mm
│ ■                   ■   │ ◄── Mounting holes
│                         │
│    M1D-TX-010A          │ ◄── Cable ID (large)
│                         │
│ 500mm² 110 XLPE CU...   │ ◄── Specification
│ FROM: M1D-TX-010A       │ ◄── Origin
│ TO: M1D-MSB-010A        │ ◄── Destination
│ ■                   ■   │
└─────────────────────────┘
         40mm
```

## Python API

```python
from generate_labels import CableLabelGenerator, CableData

# Create generator
gen = CableLabelGenerator(output_dir="./labels")

# Parse CSV
cables = gen.parse_csv("cables.csv")

# Generate single label
gen.create_label_dxf(cables[0], "label_001.dxf")

# Generate multi-label sheet
gen.create_multi_label_sheet(cables[:20], "sheet_01.dxf")

# Generate all
gen.generate_all_labels("cables.csv")
```

## Notes

- Labels are designed for **0.8mm - 1.0mm** material thickness
- Mounting holes fit M3 screws or cable ties
- Text height optimized for readability after laser engraving
- Origin/Destination text truncated to 20-25 chars to fit label

## License

MIT
