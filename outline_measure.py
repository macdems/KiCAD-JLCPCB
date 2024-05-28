import pcbnew


class MinMax1DimHolder:

    def __init__(self):
        self.min = None
        self.max = None

    def update_min_max(self, v):
        self.max = v if self.max is None else max(v, self.max)
        self.min = v if self.min is None else min(v, self.min)

    def get_distance_nm(self):
        return self.max - self.min

    def get_distance_mm(self):
        return self.get_distance_nm() / 1000000

    def get_distance_str(self):
        return str(self.get_distance_mm())  #.replace('.', 'p')

    def is_min_or_max_none(self):
        return self.min is None or self.max is None


class MinMax2DimHolder:

    def __init__(self):
        self.x = MinMax1DimHolder()
        self.y = MinMax1DimHolder()

    def update_min_max(self, point):
        self.x.update_min_max(point[0])
        self.y.update_min_max(point[1])


def has_line_on_degree(target_degree, angle_degree, angle_degree_start):
    angle_degree_end = angle_degree_start + angle_degree
    result = False
    if angle_degree > 0:
        result = (angle_degree_start <= target_degree and target_degree
                  <= angle_degree_end) or (angle_degree_start - 360 <= target_degree and target_degree <= angle_degree_end - 360)
    else:
        result = (angle_degree_end <= target_degree and target_degree
                  <= angle_degree_start) or (angle_degree_end + 360 <= target_degree and target_degree <= angle_degree_start + 360)
    return result


def get_arc_min_max_points(draw):
    # https://docs.kicad.org/doxygen-python/classpcbnew_1_1EDA__SHAPE.html
    point_center = draw.GetCenter()
    if hasattr(draw, "GetArcStart"):
        point_start = draw.GetArcStart()
    else:
        point_start = draw.GetStart()
    if hasattr(draw, "GetArcEnd"):
        point_end = draw.GetArcEnd()
    else:
        point_end = draw.GetEnd()
    points = [point_start, point_end]
    radius = draw.GetRadius()
    there_is_eda_angle = hasattr(pcbnew, "EDA_ANGLE")
    angle_degree_start = draw.GetArcAngleStart().AsDegrees() if there_is_eda_angle else draw.GetArcAngleStart() / 10
    if hasattr(draw, "GetAngle"):
        angle_degree = draw.GetAngle() / 10
    elif there_is_eda_angle and isinstance(draw.GetArcAngle(), pcbnew.EDA_ANGLE):
        angle_degree = draw.GetArcAngle().AsDegrees()
    else:
        angle_degree = draw.GetArcAngle() / 10
    if has_line_on_degree(0, angle_degree, angle_degree_start):
        points.append(pcbnew.wxPoint(point_center[0] + radius, point_center[1]))
    if has_line_on_degree(90, angle_degree, angle_degree_start):
        points.append(pcbnew.wxPoint(point_center[0], point_center[1] + radius))
    if has_line_on_degree(180, angle_degree, angle_degree_start):
        points.append(pcbnew.wxPoint(point_center[0] - radius, point_center[1]))
    if has_line_on_degree(270, angle_degree, angle_degree_start):
        points.append(pcbnew.wxPoint(point_center[0], point_center[1] - radius))
    return points


def get_min_max_2_dim_of_board(board):
    min_max_2_dim = MinMax2DimHolder()

    for draw in board.GetDrawings():
        if draw.GetClass() in ["DRAWSEGMENT", "PCB_SHAPE"] and draw.GetLayerName() == 'Edge.Cuts':
            if draw.GetShape() == pcbnew.S_ARC:
                for point in get_arc_min_max_points(draw):
                    min_max_2_dim.update_min_max(point)
            elif draw.GetShape() == pcbnew.S_CIRCLE:
                r = draw.GetRadius()
                center = draw.GetCenter()
                x = center[0]
                y = center[1]
                min_max_2_dim.update_min_max(pcbnew.wxPoint(x + r, y + r))
                min_max_2_dim.update_min_max(pcbnew.wxPoint(x - r, y - r))
            else:
                min_max_2_dim.update_min_max(draw.GetStart())
                min_max_2_dim.update_min_max(draw.GetEnd())

    return min_max_2_dim
    if min_max_2_dim.x.is_min_or_max_none() or min_max_2_dim.y.is_min_or_max_none():
        return None
    return (min_max_2_dim.x.get_distance_mm(), min_max_2_dim.y.get_distance_mm())


def get_width_height_nm_of_board(board):
    min_max_2_dim = get_min_max_2_dim_of_board(board)
    if min_max_2_dim.x.is_min_or_max_none() or min_max_2_dim.y.is_min_or_max_none():
        return None
    return (min_max_2_dim.x.get_distance_nm(), min_max_2_dim.y.get_distance_nm())


def get_width_height_mm_of_board(board):
    min_max_2_dim = get_min_max_2_dim_of_board(board)
    if min_max_2_dim.x.is_min_or_max_none() or min_max_2_dim.y.is_min_or_max_none():
        return None
    return (min_max_2_dim.x.get_distance_mm(), min_max_2_dim.y.get_distance_mm())


def create_board_size_label(board):
    wh = get_width_height_mm_of_board(board)
    return None if wh is None else f"{wh[0]+0.499999:.0f}x{wh[1]+0.499999:.0f}"


__all__ = 'create_board_size_label',
