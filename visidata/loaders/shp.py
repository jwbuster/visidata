from visidata import *
import shapefile


def open_shp(p):
    return ShapeSheet(p.name, source=p)

# pyshp doesn't care about file extensions
open_dbf = open_shp

shptypes = {
  'C': str,
  'N': float,
  'L': float,
  'F': float,
  'D': date,
  'M': str,
}

def shptype(ftype, declen):
    t = shptypes[ftype[:1]]
    if t is float and declen == 0:
        return int
    return t

# rowdef: shaperec
class ShapeSheet(Sheet):
    columns = [Column('')]
    commands = [
        Command('.', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=[cursorRow]))', ''),
        Command('g.', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=selectedRows or rows))', ''),
    ]
    @async
    def reload(self):
        sf = shapefile.Reader(self.source.resolve())
        self.columns = [
            Column('shapeType', width=0, getter=lambda col,row: row.shape.shapeType)
        ]
        self.columns += [
            Column(fname, getter=lambda col,row,i=i: row.record[i], type=shptype(ftype, declen))
                for i, (fname, ftype, fieldlen, declen) in enumerate(sf.fields[1:])  # skip DeletionFlag
        ]
        self.rows = []
        for shaperec in sf.iterShapeRecords():
            self.addRow(shaperec)


class ShapeMap(GridCanvas):
    aspectRatio = 1.0

    @async
    def reload(self):
        self.gridlines.clear()
        self.reset()

        for row in Progress(self.sourceRows):
            # color according to key
            k = tuple(col.getValue(row) for col in self.source.keyCols)

            if row.shape.shapeType == 5:
                self.polygon(row.shape.points, self.plotColor(k), row)
            else:
                status('notimpl shapeType %s' % row.shape.shapeType)

        self.refresh()
