import cv2

# 待检测的图片路径
img_path = '/home/ken/workspace/code/python3/IMG_1729.jpg'
Classifier_path = '/home/ken/lib_support/openCV/opencv/data/haarcascades/haarcascade_frontalface_default.xml'
#这个路径表示，我们下载的opencv中自带的haarcascade_frontalface_default特征集，用的时候只需
#把/media/asahi/数据/所有下载/opencv-3.3.1/，换成你自己的路径就行了

face_cascade = cv2.CascadeClassifier(Classifier_path)

# 读取图片

image = cv2.imread(img_path)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 探测图片中的人脸
faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.15,
    minNeighbors=5,
    minSize=(5, 5),
    flags=cv2.CASCADE_SCALE_IMAGE   #因为现在opencv也升级成了3，所以cv2.cv也不存在了
)


for (x, y, w, h) in faces:
    cv2.rectangle(image,(x,y),(x+w,y+w),(0,255,0),2)
    # cv2.circle(image, ((x + x + w) / 2,
    #                    (y + y + h) / 2),
    #            w / 2,
    #            (0, 255, 0),
    #            float(2))

#cv2.imshow("Find Faces!", image)
cv2.imencode('.jpg', image)[1].tofile('res.jpg')

cv2.waitKey(0)




