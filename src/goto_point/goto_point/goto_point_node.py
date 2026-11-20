#!/usr/bin/env python3
"""极简走点控制器:订阅目标点,用 TF 拿当前位姿,输出 /cmd_vel 走过去。

不使用 Nav2,只依赖定位(LiDAR SLAM 提供的 odom/map TF)。
适合滑移转向 / 差速底盘。
"""
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from tf2_ros import Buffer, TransformListener, TransformException


def yaw_from_quat(q):
    """四元数转偏航角(绕 Z)。"""
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def norm_angle(a):
    """归一化到 [-pi, pi]。"""
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


def clamp(v, limit):
    return max(-limit, min(limit, v))


class GotoPointNode(Node):
    def __init__(self):
        super().__init__('goto_point')

        # 目标点话题(兼容 RViz 的 "2D Goal Pose" 按钮,默认发 /goal_pose)
        self.goal_topic = self.declare_parameter('goal_topic', 'goal_pose').value
        # 目标点坐标默认所在帧(若 goal 的 frame_id 为空则用它)
        self.default_goal_frame = self.declare_parameter('default_goal_frame', 'odom').value
        # 机器人本体帧(用于 TF 查当前位姿)
        self.base_frame = self.declare_parameter('base_frame', 'base_footprint').value
        # 输出控制话题
        self.cmd_vel_topic = self.declare_parameter('cmd_vel_topic', 'cmd_vel').value

        # 运动学与控制参数
        self.linear_speed = self.declare_parameter('linear_speed', 0.26).value      # m/s 上限
        self.angular_speed = self.declare_parameter('angular_speed', 1.0).value     # rad/s 上限
        self.dist_tolerance = self.declare_parameter('dist_tolerance', 0.10).value  # m,到达判定
        self.angle_tolerance = self.declare_parameter('angle_tolerance', 0.10).value  # rad,先转向阈值
        self.kp_lin = self.declare_parameter('kp_lin', 0.5).value
        self.kp_ang = self.declare_parameter('kp_ang', 2.0).value
        self.control_rate = self.declare_parameter('control_rate', 20.0).value      # Hz

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.goal = None
        self.create_subscription(PoseStamped, self.goal_topic, self._goal_cb, 10)
        self.cmd_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)

        period = 1.0 / self.control_rate
        self.create_timer(period, self._control_loop)
        self.get_logger().info(
            f'goto_point 就绪: 目标话题=/{self.goal_topic}, '
            f'控制输出=/{self.cmd_vel_topic}, 本体帧={self.base_frame}'
        )

    def _goal_cb(self, msg: PoseStamped):
        self.goal = msg
        frame = msg.header.frame_id or self.default_goal_frame
        self.get_logger().info(
            f'收到目标点 ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f}) '
            f'在帧 "{frame}" 中'
        )

    def _publish(self, vx: float, wz: float):
        t = Twist()
        t.linear.x = vx
        t.angular.z = wz
        self.cmd_pub.publish(t)

    def _control_loop(self):
        if self.goal is None:
            self._publish(0.0, 0.0)
            return

        goal_frame = self.goal.header.frame_id or self.default_goal_frame

        try:
            # 机器人当前位姿(在目标帧下表达)
            tf = self.tf_buffer.lookup_transform(
                goal_frame, self.base_frame, rclpy.time.Time())
        except TransformException as e:
            self.get_logger().info(
                f'等待 TF({goal_frame} -> {self.base_frame}): {e}',
                throttle_duration_sec=3.0)
            self._publish(0.0, 0.0)
            return

        rx = tf.transform.translation.x
        ry = tf.transform.translation.y
        yaw = yaw_from_quat(tf.transform.rotation)

        dx = self.goal.pose.position.x - rx
        dy = self.goal.pose.position.y - ry
        dist = math.hypot(dx, dy)

        if dist < self.dist_tolerance:
            self._publish(0.0, 0.0)
            self.get_logger().info(
                f'✅ 已到达目标点 (剩余 {dist:.3f} m < {self.dist_tolerance} m)',
                throttle_duration_sec=1.0)
            self.goal = None  # 清空目标,等待下一个
            return

        angle_to_goal = math.atan2(dy, dx)
        angle_err = norm_angle(angle_to_goal - yaw)

        if abs(angle_err) > self.angle_tolerance:
            # 先原地转向对准目标
            vx = 0.0
            wz = clamp(self.kp_ang * angle_err, self.angular_speed)
        else:
            # 对准后前进,并带小角度修正
            vx = clamp(self.kp_lin * dist, self.linear_speed)
            wz = clamp(self.kp_ang * angle_err, self.angular_speed)

        self._publish(vx, wz)


def main(args=None):
    rclpy.init(args=args)
    node = GotoPointNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._publish(0.0, 0.0)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
