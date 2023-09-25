import cv2 as cv
import numpy as np
import openpifpaf
import PIL
from rembg import remove
import matplotlib.pyplot as plt

RESIZE_SIZE = 600  # the maximum size of the image to be processed (in pixels)


class YeadonModel:
    """A class used to represent a Yeadon Model.

    Attributes
    ----------
    keypoints : dict
        A dictionary containing the keypoints of the image. (Ls0, Ls1, ...)
    """

    def __init__(self, impath: str):
        """Creates a YeadonModel object from an image path.

        Parameters
        ----------
        impath : str
            The path to the image to be processed.

        Returns
        -------
        YeadonModel
            The YeadonModel object with the keypoints of the image.
        """
        # front
        pil_im, image, im = self._create_resize_remove_im(impath)
        edges = self._canny_edges(im, image)
        predictor = openpifpaf.Predictor(checkpoint="shufflenetv2k30-wholebody")
        predictions, gt_anns, image_meta = predictor.pil_image(pil_im)
        # You can find the index here:
        # https://github.com/jin-s13/COCO-WholeBody/blob/master/imgs/Fig2_anno.png
        # as "predictions" is an array the index starts at 0 and not at 1 like in the github
        data = predictions[0].data[:, 0:2]
        # right side
        pil_r_side_im, image_r_side, im_r_side = self._create_resize_remove_im(
            "/home/william/YeadonModelGenerator/img/al_up_r.png")
        edges_r_side = self._canny_edges(im_r_side, image_r_side)
        predictions2, gt_anns2, image_meta2 = predictor.pil_image(pil_r_side_im)
        data_r_side = predictions2[0].data[:, 0:2]
        # left side
        pil_l_side_im, image_l_side, im_l_side = self._create_resize_remove_im(
            "/home/william/YeadonModelGenerator/img/al_up_l.png")
        edges_l_side = self._canny_edges(im_l_side, image_l_side)
        predictions3, gt_anns3, image_meta3 = predictor.pil_image(pil_l_side_im)
        data_l_side = predictions3[0].data[:, 0:2]
        # front T pose but with the hand to the top
        pil_up_im, image_up, im_up = self._create_resize_remove_im(
            "/home/william/YeadonModelGenerator/img/al_front_t2.png")
        edges_up = self._canny_edges(im_up, image_up)
        predictions4, gt_anns4, image_meta4 = predictor.pil_image(pil_up_im)
        data_up = predictions4[0].data[:, 0:2]
        # front
        body_parts_index = {
            "nose": 0,
            "left_ear": 3,
            "right_ear": 4,
            "left_shoulder": 5,
            "right_shoulder": 6,
            "left_elbow": 7,
            "right_elbow": 8,
            "left_wrist": 9,
            "right_wrist": 10,
            "left_hip": 11,
            "right_hip": 12,
            "left_knee": 13,
            "right_knee": 14,
            "left_ankle": 15,
            "right_ankle": 16,
            "left_base_of_thumb": 93,
            "right_base_of_thumb": 114,
            "left_heel": 19,
            "right_heel": 22,
            "left_toe_nail": 17,
            "right_toe_nail": 20,
        }
        hand_pos = [
            96,
            100,
            104,
            108,
            117,
            121,
            125,
            129,
            98,
            102,
            106,
            110,
            119,
            123,
            127,
            131,
        ]
        body_parts_pos = {k: data[v] for k, v in body_parts_index.items()}
        # front up
        body_parts_pos_up = {k: data_up[v] for k, v in body_parts_index.items()}

        # right side
        body_parts_index_r = {
            "nose": 0,
            "right_ear": 4,
            "right_shoulder": 6,
            "right_elbow": 8,
            "right_wrist": 10,
            "right_hip": 12,
            "right_knee": 14,
            "right_ankle": 16,
            "right_base_of_thumb": 114,
            "right_heel": 22,
            "right_toe_nail": 20,
        }
        hand_pos_r = [
            117,
            121,
            125,
            129,
            119,
            123,
            127,
            131,
        ]
        body_parts_pos_r = {k: data_r_side[v] for k, v in body_parts_index_r.items()}

        # left side
        body_parts_index_l = {
            "nose": 0,
            "left_ear": 3,
            "left_shoulder": 5,
            "left_elbow": 7,
            "left_wrist": 9,
            "left_hip": 11,
            "left_knee": 13,
            "left_ankle": 15,
            "left_base_of_thumb": 93,
            "left_heel": 19,
            "left_toe_nail": 17,
        }
        hand_pos_l = [
            96,
            100,
            104,
            108,
            98,
            102,
            106,
            110,
        ]
        body_parts_pos_l = {k: data_l_side[v] for k, v in body_parts_index_l.items()}
        # front
        hand_part_pos = []
        for hand_position in hand_pos:
            hand_part_pos.append(data[hand_position])
        body_parts_pos["left_knuckles"] = np.mean(hand_part_pos[0:3], axis=0)
        body_parts_pos["right_knuckles"] = np.mean(hand_part_pos[4:7], axis=0)
        body_parts_pos["left_nails"] = np.mean(hand_part_pos[8:11], axis=0)
        body_parts_pos["right_nails"] = np.mean(hand_part_pos[12:15], axis=0)
        left_lowest_front_rib_approx = (data[5] + data[11]) / 2
        body_parts_pos["left_lowest_front_rib"] = left_lowest_front_rib_approx
        right_lowest_front_rib_approx = (data[6] + data[12]) / 2
        body_parts_pos["right_lowest_front_rib"] = right_lowest_front_rib_approx
        body_parts_pos["left_nipple"] = (left_lowest_front_rib_approx + data[5]) / 2
        body_parts_pos["right_nipple"] = (right_lowest_front_rib_approx + data[6]) / 2
        body_parts_pos["left_umbiculus"] = (
                                                   (left_lowest_front_rib_approx * 3) + (data[11] * 2)
                                           ) / 5
        body_parts_pos["right_umbiculus"] = (
                                                    (right_lowest_front_rib_approx * 3) + (data[12] * 2)
                                            ) / 5
        left_arch_approx = (data[17] + data[19]) / 2
        body_parts_pos["left_arch"] = left_arch_approx
        right_arch_approx = (data[20] + data[22]) / 2
        body_parts_pos["right_arch"] = right_arch_approx
        body_parts_pos["left_ball"] = (data[17] + left_arch_approx) / 2
        body_parts_pos["right_ball"] = (data[20] + right_arch_approx) / 2
        body_parts_pos["left_mid_arm"] = (data[5] + data[7]) / 2
        body_parts_pos["right_mid_arm"] = (data[6] + data[8]) / 2
        body_parts_pos["left_acromion"] = self._find_acromion_left(edges, data)
        body_parts_pos["right_acromion"] = self._find_acromion_right(edges, data)
        body_parts_pos["top_of_head"] = self._find_top_of_head(edges)
        body_parts_pos["right_maximum_forearm"] = self._get_maximum_point(data[10], data[8], edges)
        body_parts_pos["left_maximum_forearm"] = self._get_maximum_point(data[9], data[7], edges)
        body_parts_pos["right_maximum_calf"] = self._get_maximum_point(data[16], data[14], edges)
        body_parts_pos["left_maximum_calf"] = self._get_maximum_point(data[15], data[13], edges)
        body_parts_pos["right_crotch"], body_parts_pos["left_crotch"] = self._get_crotch_right_left(edges, data)
        body_parts_pos["right_mid_thigh"], body_parts_pos["left_mid_thigh"] = self._get_mid_thigh_right_left(data,
                                                                                                             body_parts_pos[
                                                                                                                 "right_crotch"],
                                                                                                             body_parts_pos[
                                                                                                                 "left_crotch"])
        # print(body_parts_pos)
        # front up
        left_lowest_front_rib_approx = (data_up[5] + data_up[11]) / 2
        body_parts_pos_up["left_lowest_front_rib"] = left_lowest_front_rib_approx
        right_lowest_front_rib_approx = (data_up[6] + data_up[12]) / 2
        body_parts_pos_up["right_lowest_front_rib"] = right_lowest_front_rib_approx
        body_parts_pos_up["left_nipple"] = (left_lowest_front_rib_approx + data_up[5]) / 2
        body_parts_pos_up["right_nipple"] = (right_lowest_front_rib_approx + data_up[6]) / 2
        body_parts_pos_up["left_umbiculus"] = (
                                                   (left_lowest_front_rib_approx * 3) + (data_up[11] * 2)
                                           ) / 5
        body_parts_pos_up["right_umbiculus"] = (
                                                    (right_lowest_front_rib_approx * 3) + (data_up[12] * 2)
                                            ) / 5
        left_arch_approx = (data_up[17] + data_up[19]) / 2
        body_parts_pos_up["left_arch"] = left_arch_approx
        right_arch_approx = (data_up[20] + data_up[22]) / 2
        body_parts_pos_up["right_arch"] = right_arch_approx
        body_parts_pos_up["left_ball"] = (data_up[17] + left_arch_approx) / 2
        body_parts_pos_up["right_ball"] = (data_up[20] + right_arch_approx) / 2
        body_parts_pos_up["left_mid_arm"] = (data_up[5] + data_up[7]) / 2
        body_parts_pos_up["right_mid_arm"] = (data_up[6] + data_up[8]) / 2
        body_parts_pos_up["left_acromion"] = self._find_acromion_left(edges_up, data_up)
        body_parts_pos_up["right_acromion"] = self._find_acromion_right(edges_up, data_up)
        body_parts_pos_up["top_of_head"] = self._find_top_of_head(edges_up)
        body_parts_pos_up["right_maximum_forearm"] = self._get_maximum_point(data_up[10], data_up[8], edges_up)
        body_parts_pos_up["left_maximum_forearm"] = self._get_maximum_point(data_up[9], data_up[7], edges_up)
        body_parts_pos_up["right_maximum_calf"] = self._get_maximum_point(data_up[16], data_up[14], edges_up)
        body_parts_pos_up["left_maximum_calf"] = self._get_maximum_point(data_up[15], data_up[13], edges_up)
        body_parts_pos_up["right_crotch"], body_parts_pos_up["left_crotch"] = self._get_crotch_right_left(edges_up, data_up)
        body_parts_pos_up["right_mid_thigh"], body_parts_pos_up["left_mid_thigh"] = self._get_mid_thigh_right_left(data_up,
                                                                                                             body_parts_pos_up[
                                                                                                                 "right_crotch"],
                                                                                                             body_parts_pos_up[
                                                                                                                 "left_crotch"])
        # right side
        hand_part_pos_r = []
        for hand_position in hand_pos_r:
            hand_part_pos_r.append(data_r_side[hand_position])
        body_parts_pos_r["right_knuckles"] = np.mean(hand_part_pos_r[0:3], axis=0)
        body_parts_pos_r["right_nails"] = np.mean(hand_part_pos_r[4:7], axis=0)
        right_lowest_front_rib_approx = (data_r_side[6] + data_r_side[12]) / 2
        body_parts_pos_r["right_lowest_front_rib"] = right_lowest_front_rib_approx
        body_parts_pos_r["right_nipple"] = (right_lowest_front_rib_approx + data_r_side[6]) / 2
        body_parts_pos_r["right_umbiculus"] = (
                                                      (right_lowest_front_rib_approx * 3) + (data_r_side[12] * 2)
                                              ) / 5
        right_arch_approx = (data_r_side[20] + data_r_side[22]) / 2
        body_parts_pos_r["right_arch"] = right_arch_approx
        body_parts_pos_r["right_ball"] = (data_r_side[20] + right_arch_approx) / 2
        body_parts_pos_r["right_mid_arm"] = (data_r_side[6] + data_r_side[8]) / 2

        # left side
        hand_part_pos_l = []
        for hand_position in hand_pos_l:
            hand_part_pos_l.append(data_l_side[hand_position])
        body_parts_pos_l["left_knuckles"] = np.mean(hand_part_pos_l[0:3], axis=0)
        body_parts_pos_l["left_nails"] = np.mean(hand_part_pos_l[8:11], axis=0)
        left_lowest_front_rib_approx = (data_l_side[5] + data_l_side[11]) / 2
        body_parts_pos_l["left_lowest_front_rib"] = left_lowest_front_rib_approx
        body_parts_pos_l["left_nipple"] = (left_lowest_front_rib_approx + data_l_side[5]) / 2
        body_parts_pos_l["left_umbiculus"] = (
                                                     (left_lowest_front_rib_approx * 3) + (data_l_side[11] * 2)
                                             ) / 5
        left_arch_approx = (data_l_side[17] + data_l_side[19]) / 2
        body_parts_pos_l["left_arch"] = left_arch_approx
        body_parts_pos_l["left_ball"] = (data_l_side[17] + left_arch_approx) / 2
        body_parts_pos_l["left_mid_arm"] = (data_l_side[5] + data_l_side[7]) / 2
        # print(body_parts_pos_r)
        self.keypoints = {
            "Ls0": body_parts_pos["left_hip"],
            "Ls1": body_parts_pos["left_umbiculus"],
            "Ls2": body_parts_pos["left_lowest_front_rib"],
            "Ls3": body_parts_pos["left_nipple"],
            "Ls4": body_parts_pos["left_shoulder"],
            "Ls5": body_parts_pos["left_acromion"],
            "Ls6": body_parts_pos["nose"],
            "Ls7": body_parts_pos["left_ear"],
            "Ls8": body_parts_pos["top_of_head"],
            "La0": body_parts_pos["left_shoulder"],
            "La1": body_parts_pos["left_mid_arm"],
            "La2": body_parts_pos["left_elbow"],
            "La3": body_parts_pos["left_maximum_forearm"],
            "La4": body_parts_pos["left_wrist"],
            "La5": body_parts_pos["left_base_of_thumb"],
            "La6": body_parts_pos["left_knuckles"],
            "La7": body_parts_pos["left_nails"],
            "Lb0": body_parts_pos["right_shoulder"],
            "Lb1": body_parts_pos["right_mid_arm"],
            "Lb2": body_parts_pos["right_elbow"],
            "Lb3": body_parts_pos["right_maximum_forearm"],
            "Lb4": body_parts_pos["right_wrist"],
            "Lb5": body_parts_pos["right_base_of_thumb"],
            "Lb6": body_parts_pos["right_knuckles"],
            "Lb7": body_parts_pos["right_nails"],
            "Lj0": body_parts_pos["left_hip"],
            "Lj1": body_parts_pos["left_crotch"],
            "Lj2": body_parts_pos["left_mid_thigh"],
            "Lj3": body_parts_pos["left_knee"],
            "Lj4": body_parts_pos["left_maximum_calf"],
            "Lj5": body_parts_pos["left_ankle"],
            "Lj6": body_parts_pos["left_heel"],
            "Lj7": body_parts_pos["left_arch"],
            "Lj8": body_parts_pos["left_ball"],
            "Lj9": body_parts_pos["left_toe_nail"],
            "Lk0": body_parts_pos["right_hip"],
            "Lk1": body_parts_pos["right_crotch"],
            "Lk2": body_parts_pos["right_mid_thigh"],
            "Lk3": body_parts_pos["right_knee"],
            "Lk4": body_parts_pos["right_maximum_calf"],
            "Lk5": body_parts_pos["right_ankle"],
            "Lk6": body_parts_pos["right_heel"],
            "Lk7": body_parts_pos["right_arch"],
            "Lk8": body_parts_pos["right_ball"],
            "Lk9": body_parts_pos["right_toe_nail"],
            "Ls1L": abs(body_parts_pos["left_umbiculus"][1] - body_parts_pos["left_hip"][1]),
            "Ls2L": abs(
                body_parts_pos["left_lowest_front_rib"][1]
                - body_parts_pos["left_hip"][1]
            ),
            "Ls3L": abs(
                body_parts_pos["left_nipple"][1] - body_parts_pos["left_hip"][1]
            ),
            "Ls4L": abs(
                body_parts_pos["left_shoulder"][1] - body_parts_pos["left_hip"][1]
            ),
            "Ls5L": abs(body_parts_pos["left_acromion"][1] - body_parts_pos["left_hip"][1]),
            "Ls6L": abs(body_parts_pos["left_acromion"][1] - body_parts_pos["nose"][1]),
            "Ls7L": abs(body_parts_pos["left_acromion"][1] - body_parts_pos["left_ear"][1]),
            "Ls8L": abs(
                body_parts_pos["left_acromion"][1] - body_parts_pos["top_of_head"][1]
            ),

            "Ls0p": self._stadium_perimeter(
                self._get_maximum_line(body_parts_pos["right_hip"], body_parts_pos["left_hip"], edges),
                self._get_maximum_start(body_parts_pos_r["right_hip"], body_parts_pos_r["right_umbiculus"],
                                        edges_r_side)),
            "Ls1p": self._stadium_perimeter(
                self._get_maximum_line(body_parts_pos["right_umbiculus"], body_parts_pos["left_umbiculus"], edges),
                self._get_maximum_start(body_parts_pos_r["right_umbiculus"], body_parts_pos_r["right_hip"],
                                        edges_r_side)),
            "Ls2p": self._stadium_perimeter(self._get_maximum_line(body_parts_pos["right_lowest_front_rib"],
                                                                   body_parts_pos["left_lowest_front_rib"], edges),
                                            self._get_maximum_start(body_parts_pos_r["right_lowest_front_rib"],
                                                                    body_parts_pos_r["right_hip"], edges_r_side)),
            "Ls3p": self._stadium_perimeter(
                self._get_maximum_line(body_parts_pos["right_nipple"], body_parts_pos["left_nipple"], edges),
                self._get_maximum_start(body_parts_pos_r["right_nipple"], body_parts_pos_r["right_hip"], edges_r_side)),
            "Ls5p": self._circle_perimeter(
                np.linalg.norm(body_parts_pos["left_acromion"] - body_parts_pos["right_acromion"])),
            "Ls6p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["nose"], body_parts_pos["top_of_head"], edges)),
            "Ls7p": self._circle_perimeter(np.linalg.norm(body_parts_pos["left_ear"] - body_parts_pos["right_ear"])),

            "Ls0w": self._get_maximum_line(body_parts_pos["left_hip"], body_parts_pos["right_hip"], edges),
            "Ls1w": self._get_maximum_line(body_parts_pos["left_umbiculus"], body_parts_pos["right_umbiculus"], edges),
            "Ls2w": self._get_maximum_line(body_parts_pos["left_lowest_front_rib"],
                                           body_parts_pos["right_lowest_front_rib"], edges),
            "Ls3w": self._get_maximum_line(body_parts_pos["left_nipple"], body_parts_pos["right_nipple"], edges),
            "Ls4w": np.linalg.norm(body_parts_pos["left_shoulder"] - body_parts_pos["right_shoulder"]),

            "La1L": (np.linalg.norm(body_parts_pos["left_shoulder"] - body_parts_pos["left_elbow"])) / 2,
            "La2L": np.linalg.norm(body_parts_pos["left_shoulder"] - body_parts_pos["left_elbow"]),
            "La3L": np.linalg.norm(body_parts_pos["left_shoulder"] - body_parts_pos["left_maximum_forearm"]),
            "La4L": np.linalg.norm(body_parts_pos["left_shoulder"] - body_parts_pos["left_wrist"]),
            "La5L": np.linalg.norm(body_parts_pos["left_wrist"] - body_parts_pos["left_base_of_thumb"]),
            "La6L": np.linalg.norm(body_parts_pos["left_wrist"] - body_parts_pos["left_knuckles"]),
            "La7L": np.linalg.norm(body_parts_pos["left_wrist"] - body_parts_pos["left_nails"]),

            # TODO "La0p":,
            "La1p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_mid_arm"], body_parts_pos["left_elbow"], edges)),
            "La2p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_elbow"], body_parts_pos["left_mid_arm"], edges)),
            "La3p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_maximum_forearm"], body_parts_pos["left_elbow"], edges)),
            "La4p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["left_wrist"], body_parts_pos["left_elbow"], edges), self._get_maximum_start(body_parts_pos_up["left_wrist"], body_parts_pos_up["left_elbow"], edges_up)),
            # TODO "La5p": ,
            "La6p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["left_knuckles"], body_parts_pos["left_wrist"], edges), self._get_maximum_start(data[97], body_parts_pos_up["left_wrist"], edges_up)),
            "La7p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["left_nails"], body_parts_pos["left_wrist"], edges), self._get_maximum_start(data[98], body_parts_pos_up["left_wrist"], edges_up)),

            "La4w": self._get_maximum_start(body_parts_pos["left_wrist"], body_parts_pos["left_elbow"], edges),
            "La5w": self._get_maximum_start(body_parts_pos["left_base_of_thumb"], body_parts_pos["left_wrist"], edges),
            "La6w": self._get_maximum_start(body_parts_pos["left_knuckles"], body_parts_pos["left_wrist"], edges),
            "La7w": self._get_maximum_start(body_parts_pos["left_nails"], body_parts_pos["left_wrist"], edges),

            "Lb1L": (np.linalg.norm(body_parts_pos["right_shoulder"] - body_parts_pos["right_elbow"])) / 2,
            "Lb2L": np.linalg.norm(body_parts_pos["right_shoulder"] - body_parts_pos["right_elbow"]),
            "Lb3L": np.linalg.norm(body_parts_pos["right_shoulder"] - body_parts_pos["right_maximum_forearm"]),
            "Lb4L": np.linalg.norm(body_parts_pos["right_shoulder"] - body_parts_pos["right_wrist"]),
            "Lb5L": np.linalg.norm(body_parts_pos["right_wrist"] - body_parts_pos["right_base_of_thumb"]),
            "Lb6L": np.linalg.norm(body_parts_pos["right_wrist"] - body_parts_pos["right_knuckles"]),
            "Lb7L": np.linalg.norm(body_parts_pos["right_wrist"] - body_parts_pos["right_nails"]),

            # TODO "Lb0p":,
            "Lb1p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_mid_arm"], body_parts_pos["right_elbow"], edges)),
            "Lb2p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_elbow"], body_parts_pos["right_mid_arm"], edges)),
            "Lb3p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_maximum_forearm"], body_parts_pos["right_elbow"], edges)),
            "Lb4p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["right_wrist"], body_parts_pos["right_elbow"], edges), self._get_maximum_start(body_parts_pos_up["right_wrist"], body_parts_pos_up["right_elbow"], edges_up)),
            # TODO "Lb5p":,
            "Lb6p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["right_knuckles"], body_parts_pos["right_wrist"], edges), self._get_maximum_start(data[117], body_parts_pos_up["right_wrist"], edges_up)),
            "Lb7p": self._stadium_perimeter(self._get_maximum_start(body_parts_pos["right_nails"], body_parts_pos["right_wrist"], edges), self._get_maximum_start(data[119], body_parts_pos_up["right_wrist"], edges_up)),

            "Lb4w": self._get_maximum_start(body_parts_pos["right_wrist"], body_parts_pos["right_elbow"], edges),
            # TODO "Lb5w": self._get_maximum_start(body_parts_pos["right_base_of_thumb"], body_parts_pos["right_wrist"], edges),
            "Lb6w": self._get_maximum_start(body_parts_pos["right_knuckles"], body_parts_pos["right_wrist"], edges),
            "Lb7w": self._get_maximum_start(body_parts_pos["right_nails"], body_parts_pos["right_wrist"], edges),

            "Lj1L": np.linalg.norm(body_parts_pos["left_hip"] - body_parts_pos["left_crotch"]),
            "Lj2L": (np.linalg.norm(body_parts_pos["left_hip"] - body_parts_pos["left_knee"])) / 2,
            "Lj3L": np.linalg.norm(body_parts_pos["left_hip"] - body_parts_pos["left_knee"]),
            "Lj4L": np.linalg.norm(body_parts_pos["left_hip"] - body_parts_pos["left_maximum_calf"]),
            "Lj5L": np.linalg.norm(body_parts_pos["left_hip"] - body_parts_pos["left_ankle"]),
            "Lj6L": np.linalg.norm(body_parts_pos["left_ankle"] - body_parts_pos["left_heel"]),
            "Lj7L": np.linalg.norm(body_parts_pos["left_ankle"] - body_parts_pos["left_arch"]),
            "Lj8L": np.linalg.norm(body_parts_pos["left_ankle"] - body_parts_pos["left_ball"]),
            "Lj9L": np.linalg.norm(body_parts_pos["left_ankle"] - body_parts_pos["left_toe_nail"]),

            # TODO "Lj0p": self._circle_perimeter(self._get_maximum_start(body_parts_pos["left_hip"], body_parts_pos["left_knee"], edges)),
            "Lj1p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_crotch"], body_parts_pos["left_knee"], edges)),
            "Lj2p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_mid_thigh"], body_parts_pos["left_knee"], edges)),
            "Lj3p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["left_knee"], body_parts_pos["left_hip"], edges)),
            # TODO "Lj4p":,
            # TODO "Lj5p":,
            # TODO "Lj6p":,
            # TODO "Lj7p":,
            # TODO "Lj8p":,
            # TODO "Lj9p":,

            # TODO "Lj8w":,
            # TODO "Lj9w":,

            # TODO "Lj6d":,

            "Lk1L": np.linalg.norm(body_parts_pos["right_hip"] - body_parts_pos["right_crotch"]),
            "Lk2L": (np.linalg.norm(body_parts_pos["right_hip"] - body_parts_pos["right_knee"])) / 2,
            "Lk3L": np.linalg.norm(body_parts_pos["right_hip"] - body_parts_pos["right_knee"]),
            "Lk4L": np.linalg.norm(body_parts_pos["right_hip"] - body_parts_pos["right_maximum_calf"]),
            "Lk5L": np.linalg.norm(body_parts_pos["right_hip"] - body_parts_pos["right_ankle"]),
            "Lk6L": np.linalg.norm(body_parts_pos["right_ankle"] - body_parts_pos["right_heel"]),
            "Lk7L": np.linalg.norm(body_parts_pos["right_ankle"] - body_parts_pos["right_arch"]),
            "Lk8L": np.linalg.norm(body_parts_pos["right_ankle"] - body_parts_pos["right_ball"]),
            "Lk9L": np.linalg.norm(body_parts_pos["right_ankle"] - body_parts_pos["right_toe_nail"]),

            # TODO "Lk0p": self._circle_perimeter(self._get_maximum_start(body_parts_pos["right_hip"], body_parts_pos["right_knee"], edges)),
            "Lk1p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_crotch"], body_parts_pos["right_knee"], edges)),
            "Lk2p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_mid_thigh"], body_parts_pos["right_hip"], edges)),
            "Lk3p": self._circle_perimeter(
                self._get_maximum_start(body_parts_pos["right_knee"], body_parts_pos["right_hip"], edges)),
            # TODO "Lk4p":,
            # TODO "Lk5p":,
            # TODO "Lk6p":,
            # TODO "Lk7p":,
            # TODO "Lk8p":,
            # TODO "Lk9p":,

            # TODO "Lk8w":,
            # TODO "Lk9w":,

            # TODO "Lk6d":,
        }
        print(self.keypoints)

    def _get_maximum(self, start, end, edges, angle, is_start):
        def pt_from(origin, angle, distance):
            """
            compute the point [x, y] that is 'distance' apart from the origin point
            perpendicular
            """
            x = origin[1] + np.sin(angle) * distance
            y = origin[0] + np.cos(angle) * distance
            return np.array([int(y), int(x)])

        def find_edge(p1, p2, angle_radians):
            distance = 0
            save = []
            while True:
                # as we want the width of the "start", we choose p1
                x, y = pt_from(p1, angle_radians, distance)
                if x < 0 or x >= edges.shape[0] or y < 0 or y >= edges.shape[1]:
                    break
                hit_zone = edges[x, y] == 255
                if np.any(hit_zone):
                    save.append((y, x))
                    break

                distance += 0.01
            return save

        def get_points(start, end):
            p1 = start[0:2]
            p1 = np.array([p1[1], p1[0]])
            p2 = end[0:2]
            p2 = np.array([p2[1], p2[0]])
            return np.array([p1, p2])

        p1, p2 = get_points(start, end)
        vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        angle_radians = np.arctan2(vector[1], vector[0]) - angle
        max1 = find_edge(p1, p2, angle_radians)
        angle_radians = (np.arctan2(vector[1], vector[0]) + angle) * is_start
        max2 = find_edge(p1, p2, angle_radians)
        return np.linalg.norm(np.array(max1) - np.array(max2))

    def _get_maximum_line(self, start, end, edges):
        return self._get_maximum(start, end, edges, 0, -1)

    def _get_maximum_start(self, start, end, edges):
        return self._get_maximum(start, end, edges, np.pi / 2, 1)

    def _get_maximum_point(self, start, end, edges):
        def pt_from(origin, angle, distance):
            """
            compute the point [x, y] that is 'distance' apart from the origin point
            perpendicular
            """
            x = origin[1] + np.sin(angle) * distance
            y = origin[0] + np.cos(angle) * distance
            return np.array([int(y), int(x)])

        def get_max_approx(top_arr, bottom_arr):
            if len(top_arr) != len(bottom_arr):
                print("error not the same nbr of pts")
                return
            max_norm = 0
            save_index = 0
            vector = np.array(top_arr) - np.array(bottom_arr)
            norms = np.linalg.norm(vector, axis=1)
            for i in range(len(top_arr)):
                if norms[i] > max_norm:
                    max_norm = norms[i]
                    save_index = i
            return save_index

        def get_points(start, end):
            p1 = start[0:2]
            p1 = np.array([p1[1], p1[0]])
            p2 = end[0:2]
            p2 = np.array([p2[1], p2[0]])
            return np.array([p1, p2])

        def vector_angle_plus(p1, p2):
            vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            angle_radians = np.arctan2(vector[1], vector[0]) + np.pi / 2
            return angle_radians

        def vector_angle_minus(p1, p2):
            vector = np.array([p2[0] - p1[0], p2[1] - p1[1]])
            angle_radians = np.arctan2(vector[1], vector[0]) - np.pi / 2
            return angle_radians

        def get_maximum_range(p1, p2, angle_radians):
            save = []
            # for all the points between p1 and p2
            for point in result:
                distance = 0
                while True:

                    x, y = pt_from(point, angle_radians, distance)
                    if x < 0 or x >= edges.shape[0] or y < 0 or y >= edges.shape[1]:
                        break

                    # Check if we've found an edge pixel
                    # hit_zone = edges[y-1:y+2, x-1:x+2] == 255# 3 x 3
                    hit_zone = edges[x, y] == 255
                    if np.any(hit_zone):
                        save.append((y, x))
                        break

                    distance += 0.01
            return save

        # get the maximums for calf and forearm
        p1, p2 = get_points(start, end)
        # create an array with 100 points between start and end
        x_values = np.linspace(p1[1], p2[1], 100)
        y_values = np.linspace(p1[0], p2[0], 100)
        result = [(y, x) for x, y in zip(x_values, y_values)]
        # set the angle in the direction of the edges
        angle_radians = vector_angle_plus(p1, p2)
        r_side = get_maximum_range(p1, p2, angle_radians)
        # set the angle in the direction of other side
        angle_radians = vector_angle_minus(p1, p2)
        l_side = get_maximum_range(p1, p2, angle_radians)
        # get the index of the max
        index = get_max_approx(r_side, l_side)
        return result[index][::-1]

    def _get_crotch_right_left(self, edges, data):
        def crop(image, position_1, position_2):
            """Return the cropped image given two positions.

            Parameters
            ----------
            image : numpy array
                The image to be cropped.
            position_1 : tuple
                The position of the first corner of the image to be cropped.
            position_2 : tuple
                The position of the second corner of the image to be cropped.

            Returns
            -------
            numpy array
                The cropped image.
            """
            x1, y1 = map(int, position_1[0:2])
            x2, y2 = map(int, position_2[0:2])
            if x1 > x2:
                x2, x1 = x1, x2
            if y1 > y2:
                y2, y1 = y1, y2
            x = image[y1:y2, x1:x2].copy()
            return x

        # crop the image to see the right hip to the left knee
        crotch_zone = crop(edges, data[12], data[13])
        # now the cropped image only has the crotch as an edge so we can get it like the head
        crotch_approx_crop = np.where(crotch_zone != 0)[1][0], np.where(crotch_zone != 0)[0][1]
        crotch_approx_right = np.array([data[12][0], data[12][1] + crotch_approx_crop[1]])
        crotch_approx_left = np.array([data[11][0], data[11][1] + crotch_approx_crop[1]])
        return crotch_approx_right, crotch_approx_left

    def _get_mid_thigh_right_left(self, data, r_crotch, l_crotch):
        mid_thigh_right = (data[14][0:2] + r_crotch) / 2
        mid_thigh_left = (data[13][0:2] + l_crotch) / 2
        return mid_thigh_right, mid_thigh_left

    def _find_acromion_right(self, edges, data):
        """Finds the acromion given an image and a set of keypoints.

        Parameters
        ----------
        im : numpy array
            The image to be processed.
        data : numpy array
            The keypoints of the image (given by openpifpaf WholeBody, predictions[0].data generally).

        Returns
        -------
        numpy array
            The coordinates of the acromion in the image.
        """

        def crop(image, position_1, position_2):
            """Return the cropped image given two positions.

            Parameters
            ----------
            image : numpy array
                The image to be cropped.
            position_1 : tuple
                The position of the first corner of the image to be cropped.
            position_2 : tuple
                The position of the second corner of the image to be cropped.

            Returns
            -------
            numpy array
                The cropped image.
            """
            x1, y1 = map(int, position_1[0:2])
            x2, y2 = map(int, position_2[0:2])
            if x1 > x2:
                x2, x1 = x1, x2
            if y1 > y2:
                y2, y1 = y1, y2
            return image[y1:y2, x1:x2].copy()

        r_ear, r_shoulder = data[4], data[6]
        cropped_img = crop(edges, r_ear, r_shoulder)
        cropped_img[:int(len(cropped_img) / 2), :] = 0
        cropped_img[:, :int(len(cropped_img[0]) / 2)] = 0
        acromion = np.array(
            [r_ear[0] - np.where(cropped_img == 255)[1][0], r_ear[1] + np.where(cropped_img == 255)[0][0]])
        return acromion

    def _find_acromion_left(self, edges, data):
        """Finds the acromion given an image and a set of keypoints.

        Parameters
        ----------
        im : numpy array
            The image to be processed.
        data : numpy array
            The keypoints of the image (given by openpifpaf WholeBody, predictions[0].data generally).

        Returns
        -------
        numpy array
            The coordinates of the acromion in the image.
        """

        def crop(image, position_1, position_2):
            """Return the cropped image given two positions.

            Parameters
            ----------
            image : numpy array
                The image to be cropped.
            position_1 : tuple
                The position of the first corner of the image to be cropped.
            position_2 : tuple
                The position of the second corner of the image to be cropped.

            Returns
            -------
            numpy array
                The cropped image.
            """
            x1, y1 = map(int, position_1[0:2])
            x2, y2 = map(int, position_2[0:2])
            if x1 > x2:
                x2, x1 = x1, x2
            if y1 > y2:
                y2, y1 = y1, y2
            return image[y1:y2, x1:x2].copy()

        l_ear, l_shoulder = data[3], data[5]
        cropped_img = crop(edges, l_ear, l_shoulder)
        cropped_img[:int(len(cropped_img) / 2), :] = 0
        cropped_img[:, :int(len(cropped_img[0]) / 2)] = 0
        acromion = np.array(
            [l_ear[0] + np.where(cropped_img == 255)[1][0], l_ear[1] + np.where(cropped_img == 255)[0][0]])
        return acromion

    def _find_top_of_head(self, edges):
        """Finds the top of the head given an image.

        Parameters
        ----------
        image : numpy array
            The image to be processed.

        Returns
        -------
        numpy array
            The coordinates of the top of the head in the image.
        """
        # the first pixel from top to bottom to find the top_of_head
        top_of_head = [
            np.where(edges != 0)[1][0],
            np.where(edges != 0)[0][0],
        ]
        return top_of_head

    def _stadium_perimeter(self, width, depth):
        radius = depth / 2
        a = width - depth
        perimeter = 2 * (np.pi * radius + a)
        return perimeter

    def _circle_perimeter(self, diag):
        r = diag / 2
        return 2 * np.pi * r

    def _resize(self, im):
        """Resizes an image given a maximum size of RESIZE_SIZE.

        Parameters
        ----------
        im : PIL Image
            The image to be resized.

        Returns
        -------
        PIL Image
            The resized image.
        """
        x_im, y_im = im.height, im.width
        x_ratio, y_ratio = RESIZE_SIZE / x_im, RESIZE_SIZE / y_im
        min_ratio = min(x_ratio, y_ratio)
        if min_ratio >= 1:
            return im.copy()
        x_resize, y_resize = int(min_ratio * x_im), int(min_ratio * y_im)
        return im.resize((y_resize, x_resize))

    def _canny_edges(self, im, image):
        grayscale_image = cv.cvtColor(im, cv.COLOR_BGR2GRAY)
        edged = cv.Canny(grayscale_image, 10, 100)

        # define a (3, 3) structuring element
        kernel = cv.getStructuringElement(cv.MORPH_RECT, (3, 3))

        # apply the dilation operation to the edged image
        dilate = cv.dilate(edged, kernel, iterations=1)

        # find the contours in the dilated image
        contours, _ = cv.findContours(dilate, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        edges = np.zeros(image.shape)
        # draw the contours on a copy of the original image
        cv.drawContours(edges, contours, -1, (0, 255, 0), 2)
        return edges

    def _create_resize_remove_im(self, impath):
        pil_im = PIL.Image.open(impath).convert("RGB")
        pil_im = self._resize(pil_im)
        image = np.asarray(pil_im)
        im = remove(image)
        return pil_im, image, im


if __name__ == "__main__":
    pass
