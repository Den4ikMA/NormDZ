import numpy as np
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

# === 1. Загрузка и подготовка данных ===
# Загрузка MNIST
def load_data():
    mnist = fetch_openml('mnist_784', version=1)
    X = mnist.data / 255.0  # Нормализация данных (диапазон [0, 1])
    y = mnist.target.astype(int)  # Метки классов
    return X, y

# One-Hot Encoding для меток классов
def preprocess_data(X, y):
    encoder = OneHotEncoder(sparse_output=False)
    y_one_hot = encoder.fit_transform(y.values.reshape(-1, 1))
    return X, y_one_hot

# Разделение на обучающую и тестовую выборки
X, y = load_data()
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train, y_train_one_hot = preprocess_data(X_train, y_train)
X_test, y_test_one_hot = preprocess_data(X_test, y_test)

# === 2. Реализация персептрона с двумя скрытыми слоями ===
class MultiLayerPerceptron:
    def __init__(self, input_size, hidden_size1, hidden_size2, output_size):
        # Инициализация весов случайными значениями
        self.weights_input_hidden1 = np.random.rand(input_size, hidden_size1) - 0.5
        self.weights_hidden1_hidden2 = np.random.rand(hidden_size1, hidden_size2) - 0.5
        self.weights_hidden2_output = np.random.rand(hidden_size2, output_size) - 0.5
        self.learning_rate = 0.05

    def relu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, x):
        return (x > 0).astype(float)


    def forward(self, x):
        # Прямое распространение через первый скрытый слой
        self.hidden_layer1_activation = np.dot(x, self.weights_input_hidden1)
        self.hidden_layer1_output = self.relu(self.hidden_layer1_activation)

        # Прямое распространение через второй скрытый слой
        self.hidden_layer2_activation = np.dot(self.hidden_layer1_output, self.weights_hidden1_hidden2)
        self.hidden_layer2_output = self.relu(self.hidden_layer2_activation)

        # Прямое распространение на выходной слой
        self.output_layer_activation = np.dot(self.hidden_layer2_output, self.weights_hidden2_output)
        self.output_layer_output = self.relu(self.output_layer_activation)
        
        return self.output_layer_output

    def backward(self, x, y):
        # Ошибка на выходном слое
        output_error = y - self.output_layer_output
        output_delta = output_error * self.relu_derivative(self.output_layer_output)

        # Ошибка на втором скрытом слое
        hidden2_error = output_delta.dot(self.weights_hidden2_output.T)
        hidden2_delta = hidden2_error * self.relu_derivative(self.hidden_layer2_output)

        # Ошибка на первом скрытом слое
        hidden1_error = hidden2_delta.dot(self.weights_hidden1_hidden2.T)
        hidden1_delta = hidden1_error * self.relu_derivative(self.hidden_layer1_output)

        # Обновление весов
        self.weights_hidden2_output += self.hidden_layer2_output.T.dot(output_delta) * self.learning_rate
        self.weights_hidden1_hidden2 += self.hidden_layer1_output.T.dot(hidden2_delta) * self.learning_rate
        self.weights_input_hidden1 += x.T.dot(hidden1_delta) * self.learning_rate

    def train(self, x_train, y_train, epochs):
        for epoch in range(epochs):
            for i in range(len(x_train)):
                x = x_train.iloc[i].values.reshape(1, -1)  # Используем iloc для доступа к строкам
                y = y_train[i].reshape(1, -1)
                self.forward(x)
                self.backward(x, y)

            if epoch % 10 == 0:
                loss = np.mean(np.square(y_train - [self.forward(x) for x in x_train.values]))
                print(f"Epoch {epoch}, Loss: {loss:.4f}")

    def predict(self, x):
        output = self.forward(x)
        return np.argmax(output)

# === 3. Обучение модели ===
input_size = X_train.shape[1]  # Размер входных данных (784 для MNIST)
hidden_size1 = 128              # Количество нейронов в первом скрытом слое (можно менять)
hidden_size2 = 64               # Количество нейронов во втором скрытом слое (можно менять)
output_size = 10                # Количество классов (цифры от 0 до 9)

mlp = MultiLayerPerceptron(input_size=input_size,
                            hidden_size1=hidden_size1,
                            hidden_size2=hidden_size2,
                            output_size=output_size)

print("Начало обучения...")
mlp.train(X_train, y_train_one_hot, epochs=50)  # Используем подвыборку для примера

# === 4. Тестирование модели ===
correct_predictions = sum(mlp.predict(X_test.iloc[i].values) == np.argmax(y_test.iloc[i]) for i in range(len(X_test)))
accuracy = correct_predictions / len(X_test)
print(f'Accuracy on test set: {accuracy * 100:.2f}%')
