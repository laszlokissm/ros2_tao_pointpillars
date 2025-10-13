import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection3DArray
from visualization_msgs.msg import Marker, MarkerArray

class Detection3DVisualizer(Node):
    def __init__(self):
        super().__init__('detection3d_visualizer')
        self.subscription = self.create_subscription(
            Detection3DArray,
            'bbox',
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(MarkerArray, 'visualization_marker_array', 10)
        
    def listener_callback(self, msg):
        marker_array = MarkerArray()
        
        # First, delete all previous markers
        delete_marker = Marker()
        delete_marker.action = Marker.DELETEALL
        marker_array.markers.append(delete_marker)
        
        i = 0
        confidence_threshold = 0.0 # Hardcoded threshold
        
        for detection in msg.detections:
            # Get the highest confidence score from detection results
            max_score = 0.0
            if detection.results:
                for result in detection.results:
                    if result.hypothesis:
                        # hypothesis is a single ObjectHypothesis, not a list
                        if result.hypothesis.score > max_score:
                            max_score = result.hypothesis.score
            
            # Only create marker if score is above threshold
            if max_score >= confidence_threshold:
                marker = Marker()
                marker.header = msg.header
                marker.ns = 'detections'
                # marker.id = detection.id
                marker.id = i
                marker.type = Marker.LINE_LIST
                marker.action = Marker.ADD
                marker.pose = detection.bbox.center
                # Shift boxes down by 0.33m to align with base_link coordinate system
                marker.pose.position.z = detection.bbox.center.position.z - 0.81
                marker.scale.x = 0.05  # Line thickness
                marker.color.a = 1.0  # Solid lines
                marker.color.r = 1.0
                marker.color.g = 0.0
                marker.color.b = 0.0
                
                # Create wireframe by defining the 12 edges of a cube
                from geometry_msgs.msg import Point
                
                # Get half dimensions
                hx = detection.bbox.size.x / 2.0
                hy = detection.bbox.size.y / 2.0
                hz = detection.bbox.size.z / 2.0
                
                # Define 8 corners of the cube (relative to center)
                corners = [
                    Point(x=-hx, y=-hy, z=-hz),  # 0: bottom-back-left
                    Point(x=hx,  y=-hy, z=-hz),  # 1: bottom-back-right
                    Point(x=hx,  y=hy,  z=-hz),  # 2: bottom-front-right
                    Point(x=-hx, y=hy,  z=-hz),  # 3: bottom-front-left
                    Point(x=-hx, y=-hy, z=hz),   # 4: top-back-left
                    Point(x=hx,  y=-hy, z=hz),   # 5: top-back-right
                    Point(x=hx,  y=hy,  z=hz),   # 6: top-front-right
                    Point(x=-hx, y=hy,  z=hz),   # 7: top-front-left
                ]
                
                # Define 12 edges (each edge needs 2 points)
                edges = [
                    # Bottom face edges
                    (0, 1), (1, 2), (2, 3), (3, 0),
                    # Top face edges  
                    (4, 5), (5, 6), (6, 7), (7, 4),
                    # Vertical edges
                    (0, 4), (1, 5), (2, 6), (3, 7)
                ]
                
                # Add all edge points to the marker
                marker.points = []
                for edge in edges:
                    marker.points.append(corners[edge[0]])
                    marker.points.append(corners[edge[1]])
                
                #if max_score > 0.5:
                #    marker.color.r = 0.0
                #    marker.color.g = 1.0
                #    marker.color.b = 0.0
                
                marker.lifetime = rclpy.duration.Duration(seconds = 0).to_msg()  # Permanent markers
                marker_array.markers.append(marker)
                i+=1
        
        self.publisher.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)
    node = Detection3DVisualizer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()