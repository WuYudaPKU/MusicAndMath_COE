> 如果有新的想法，写在issues里面(推荐)，或者修改fitness_function.py然后提交pull requests.

现在我们的函数组成是这样的：所有有关训练和音乐的参数，在config.py中有很详细的注释介绍，可以通过调整config.py来调整训练偏好；

util.py中是调用的工具函数，不要修改；

fitness_function.py中是适应度函数，可以进行修改。可以按照任意和弦走向进行（运行后的交互式页面）。

main.py是一个乐句的训练主程序，启动main.py会开始训练，给出一段四个小节的乐句。

composer.py是组成乐章的核心函数，可以先生成旋律A，然后生成变体A'，接着给出B，最后回到A。总体效果比一个乐句要好很多。
