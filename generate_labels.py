#!/usr/bin/env python3
"""
Cable Label Generator from CSV
Generate DXF labels for cable tagging from CSV schedule
"""

import csv
import os
import sys
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional
import ezdxf
from ezdxf import units


@dataclass
class CableData:
    """Cable data structure"""
    cable_id: str
    specification: str
    origin: str
    destination: str
    size: str = ""
    type: str = ""
    
    def __post_init__(self):
        # Parse specification to extract size and type
        # Format: "500mm² 110 XLPE CU FLEX 20-OF"
        spec_parts = self.specification.split()
        if spec_parts:
            # First part is usually size like "500mm²"
            self.size = spec_parts[0] if 'mm' in spec_parts[0] else ""
            # Rest is type
            self.type = ' '.join(spec_parts[1:]) if len(spec_parts) > 1 else ""


class CableLabelGenerator:
    """Generate DXF cable labels from CSV data"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.canvas_width = 600  # mm
        self.canvas_height = 300  # mm
        
        # Label dimensions (180mm x 45mm - corrected size)
        self.label_width = 180  # mm
        self.label_height = 45  # mm
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def parse_csv(self, csv_path: str) -> List[CableData]:
        """Parse CSV file and return list of CableData"""
        cables = []
        
        # Detect encoding
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(csv_path, 'r', encoding=encoding) as f:
                    # Try to detect if there's a header
                    sample = f.read(1024)
                    f.seek(0)
                    
                    # Check if first line looks like header
                    first_line = sample.split('\n')[0] if sample else ""
                    has_header = any(keyword in first_line.lower() for keyword in 
                                   ['cable', 'id', 'origin', 'destination', 'spec'])
                    
                    reader = csv.reader(f)
                    
                    # Skip header if exists
                    if has_header:
                        next(reader)
                    
                    for row in reader:
                        if len(row) >= 4:
                            cable = CableData(
                                cable_id=row[0].strip(),
                                specification=row[1].strip(),
                                origin=row[2].strip().replace('ORIGIN: ', ''),
                                destination=row[3].strip().replace('DESTINATION: ', '')
                            )
                            if cable.cable_id:  # Only add if has ID
                                cables.append(cable)
                        elif len(row) >= 2:
                            # Handle simpler format
                            cable = CableData(
                                cable_id=row[0].strip(),
                                specification=row[1].strip(),
                                origin=row[2].strip() if len(row) > 2 else "",
                                destination=row[3].strip() if len(row) > 3 else ""
                            )
                            if cable.cable_id:
                                cables.append(cable)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading with {encoding}: {e}")
                continue
        
        return cables
    
    def create_label_dxf(self, cable: CableData, filename: str, 
                         label_width: float = 80, label_height: float = 40) -> str:
        """Create single label DXF file"""
        
        doc = ezdxf.new('R2010')  # AutoCAD 2010+ compatible
        msp = doc.modelspace()
        
        # Set units to millimeters
        doc.units = units.MM
        
        # Create layers
        doc.layers.add("Cutting", color=4)   # Cyan
        doc.layers.add("Hole", color=1)      # Red
        doc.layers.add("Text", color=5)      # Blue
        
        # Draw label outline (cutting line)
        points = [
            (0, 0),
            (label_width, 0),
            (label_width, label_height),
            (0, label_height),
            (0, 0)
        ]
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "Cutting"})
        
        # Add mounting holes (4 corners, 5mm from edges)
        hole_offset = 5
        hole_width = 5   # mm
        hole_height = 2.5  # mm
        hole_positions = [
            (hole_offset, hole_offset),
            (label_width - hole_offset, hole_offset),
            (hole_offset, label_height - hole_offset),
            (label_width - hole_offset, label_height - hole_offset)
        ]

        for hx, hy in hole_positions:
            # Draw rectangle hole (5mm x 2.5mm)
            hole_points = [
                (hx - hole_width/2, hy - hole_height/2),
                (hx + hole_width/2, hy - hole_height/2),
                (hx + hole_width/2, hy + hole_height/2),
                (hx - hole_width/2, hy + hole_height/2),
                (hx - hole_width/2, hy - hole_height/2)
            ]
            msp.add_lwpolyline(hole_points, close=True, dxfattribs={"layer": "Hole"})
        
        # Add text - Layout matching MLA sample DXF style (180mm x 45mm)
        text_margin = 5
        
        # Cable ID (top, larger font, centered)
        msp.add_text(
            cable.cable_id,
            height=7,
            dxfattribs={
                "layer": "Text",
                "style": "STANDARD",
                "insert": (label_width/2, label_height - 12),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE
            }
        )
        
        # Specification (below cable ID) - wider label allows longer text
        spec_text = cable.specification[:55] if len(cable.specification) > 55 else cable.specification
        msp.add_text(
            spec_text,
            height=4,
            dxfattribs={
                "layer": "Text",
                "insert": (label_width/2, label_height - 22),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE
            }
        )
        
        # Origin (left aligned, bottom section) - wider label allows longer text
        if cable.origin:
            origin_short = cable.origin[:45] if len(cable.origin) > 45 else cable.origin
            msp.add_text(
                f"ORIGIN: {origin_short}",
                height=3.5,
                dxfattribs={
                    "layer": "Text",
                    "insert": (text_margin, 14),
                    "valign": ezdxf.const.MIDDLE
                }
            )
        
        # Destination (left aligned, below origin)
        if cable.destination:
            dest_short = cable.destination[:45] if len(cable.destination) > 45 else cable.destination
            msp.add_text(
                f"DEST: {dest_short}",
                height=3.5,
                dxfattribs={
                    "layer": "Text",
                    "insert": (text_margin, 7),
                    "valign": ezdxf.const.MIDDLE
                }
            )
        
        # Save file
        output_path = os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
    
    def create_multi_label_sheet(self, cables: List[CableData], filename: str,
                                  labels_per_row: int = 6, 
                                  label_width: float = 80,
                                  label_height: float = 40,
                                  spacing: float = 2) -> str:
        """Create multi-label sheet arranged in grid"""
        
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        doc.units = units.MM
        
        # Create layers
        doc.layers.add("Cutting", color=4)
        doc.layers.add("Hole", color=1)
        doc.layers.add("Text", color=5)
        
        # Calculate layout
        total_width = labels_per_row * (label_width + spacing) + spacing
        rows_needed = (len(cables) + labels_per_row - 1) // labels_per_row
        total_height = rows_needed * (label_height + spacing) + spacing
        
        print(f"Creating sheet: {total_width:.0f}mm x {total_height:.0f}mm")
        print(f"Labels: {len(cables)} arranged in {rows_needed} rows x {labels_per_row} cols")
        
        for idx, cable in enumerate(cables):
            row = idx // labels_per_row
            col = idx % labels_per_row
            
            x_offset = spacing + col * (label_width + spacing)
            y_offset = total_height - (row + 1) * (label_height + spacing)
            
            self._draw_label_at_position(
                msp, cable, x_offset, y_offset, 
                label_width, label_height
            )
        
        output_path = os.path.join(self.output_dir, filename)
        doc.saveas(output_path)
        return output_path
    
    def _draw_label_at_position(self, msp, cable: CableData, 
                                 x: float, y: float,
                                 width: float, height: float):
        """Draw a single label at specified position"""
        
        # Outline
        points = [
            (x, y),
            (x + width, y),
            (x + width, y + height),
            (x, y + height),
            (x, y)
        ]
        msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "Cutting"})
        
        # Mounting holes
        hole_offset = 5
        hole_width = 5   # mm
        hole_height = 2.5  # mm
        hole_positions = [
            (x + hole_offset, y + hole_offset),
            (x + width - hole_offset, y + hole_offset),
            (x + hole_offset, y + height - hole_offset),
            (x + width - hole_offset, y + height - hole_offset)
        ]
        
        for hx, hy in hole_positions:
            # Draw rectangle hole (5mm x 2.5mm)
            hole_points = [
                (hx - hole_width/2, hy - hole_height/2),
                (hx + hole_width/2, hy - hole_height/2),
                (hx + hole_width/2, hy + hole_height/2),
                (hx - hole_width/2, hy + hole_height/2),
                (hx - hole_width/2, hy - hole_height/2)
            ]
            msp.add_lwpolyline(hole_points, close=True, dxfattribs={"layer": "Hole"})
        
        # Text content
        text_margin = 3
        
        # Cable ID (centered, large)
        msp.add_text(
            cable.cable_id,
            height=6,
            dxfattribs={
                "layer": "Text",
                "insert": (x + width/2, y + height - 12),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE
            }
        )
        
        # Specification - wider label allows longer text
        spec = cable.specification[:50] if len(cable.specification) > 50 else cable.specification
        msp.add_text(
            spec,
            height=3.5,
            dxfattribs={
                "layer": "Text",
                "insert": (x + width/2, y + height - 22),
                "halign": ezdxf.const.CENTER,
                "valign": ezdxf.const.MIDDLE
            }
        )
        
        # Origin (left aligned, bottom section) - MLA sample style
        if cable.origin:
            origin_short = cable.origin[:40] if len(cable.origin) > 40 else cable.origin
            msp.add_text(
                f"ORIGIN: {origin_short}",
                height=3.2,
                dxfattribs={
                    "layer": "Text",
                    "insert": (x + text_margin, y + 12),
                    "valign": ezdxf.const.MIDDLE
                }
            )
        
        # Destination (left aligned, below origin)
        if cable.destination:
            dest_short = cable.destination[:40] if len(cable.destination) > 40 else cable.destination
            msp.add_text(
                f"DEST: {dest_short}",
                height=3.2,
                dxfattribs={
                    "layer": "Text",
                    "insert": (x + text_margin, y + 6),
                    "valign": ezdxf.const.MIDDLE
                }
            )
    
    def generate_all_labels(self, csv_path: str, 
                           individual: bool = False,
                           combined: bool = True) -> List[str]:
        """Generate all labels from CSV"""
        
        print(f"\n{'='*60}")
        print(f"CABLE LABEL GENERATOR")
        print(f"{'='*60}")
        print(f"CSV File: {csv_path}")
        print(f"Output Directory: {self.output_dir}")
        print(f"{'='*60}\n")
        
        # Parse CSV
        cables = self.parse_csv(csv_path)
        print(f"✓ Found {len(cables)} cables in CSV\n")
        
        if not cables:
            print("❌ No cables found!")
            return []
        
        generated_files = []
        
        # Show sample
        print("Sample cables:")
        for i, cable in enumerate(cables[:5], 1):
            print(f"  {i}. {cable.cable_id}")
            print(f"     Spec: {cable.specification}")
            print(f"     {cable.origin} → {cable.destination}")
        print()
        
        # Generate individual labels
        if individual:
            print("Generating individual labels...")
            for i, cable in enumerate(cables, 1):
                filename = f"cable_{cable.cable_id.replace('/', '_')}.dxf"
                filepath = self.create_label_dxf(cable, filename)
                generated_files.append(filepath)
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(cables)}")
            print(f"✓ Generated {len(cables)} individual labels\n")
        
        # Generate combined sheets
        if combined:
            print("Generating combined label sheets...")
            
            # Calculate layout for 180mm x 45mm labels on 600x300mm canvas
            # 600 / (180 + 2) = ~3.3 → 3 labels per row
            # 300 / (45 + 2) = ~6.4 → 6 rows
            # Total: 3 x 6 = 18 labels per sheet
            batch_size = 18
            batches = [cables[i:i+batch_size] 
                      for i in range(0, len(cables), batch_size)]
            
            for batch_num, batch in enumerate(batches, 1):
                filename = f"cable_labels_sheet_{batch_num:02d}.dxf"
                filepath = self.create_multi_label_sheet(
                    batch, filename,
                    labels_per_row=3,
                    label_width=180,
                    label_height=45,
                    spacing=2
                )
                generated_files.append(filepath)
                print(f"  ✓ Sheet {batch_num}: {len(batch)} labels")
            
            print(f"✓ Generated {len(batches)} combined sheets\n")
        
        # Summary
        print(f"{'='*60}")
        print(f"GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Total files: {len(generated_files)}")
        print(f"Output location: {os.path.abspath(self.output_dir)}")
        print(f"{'='*60}\n")
        
        return generated_files


def main():
    parser = argparse.ArgumentParser(
        description='Generate DXF cable labels from CSV schedule'
    )
    parser.add_argument('csv_file', help='Path to CSV file')
    parser.add_argument('-o', '--output', default='output',
                       help='Output directory (default: output)')
    parser.add_argument('--individual', action='store_true',
                       help='Generate individual DXF files for each cable')
    parser.add_argument('--no-combined', action='store_true',
                       help='Skip combined sheets generation')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"❌ Error: File not found: {args.csv_file}")
        sys.exit(1)
    
    generator = CableLabelGenerator(output_dir=args.output)
    generator.generate_all_labels(
        args.csv_file,
        individual=args.individual,
        combined=not args.no_combined
    )


if __name__ == '__main__':
    main()
