import pandas as pd
import torch
import torch.nn as nn
import cv2
import numpy as np
import torch.optim as optim
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import mean_absolute_percentage_error


# used the csv file for testing 
# use the graph queries after to us the data and what not 
file_path = "sales_modified5.csv"  
df = pd.read_csv(file_path)

df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = df['datetime'].dt.date

# calculate the total sales per day 
daily_sales = df.groupby('date')['total'].sum().reset_index()
daily_sales.columns = ['Date', 'Total Sales']

# Normalise sales data
scaler = MinMaxScaler()
daily_sales['Total Sales'] = scaler.fit_transform(daily_sales[['Total Sales']])  # Double brackets make it 2D


# Split data into training, validation, and test sets based on 70/15/15
train_size = int(len(daily_sales) * 0.7)
val_size = int(len(daily_sales) * 0.15)
test_size = len(daily_sales) - train_size - val_size

train_sales = torch.tensor(daily_sales['Total Sales'].values[:train_size], dtype=torch.float32).unsqueeze(0)
val_sales = torch.tensor(daily_sales['Total Sales'].values[train_size:train_size + val_size], dtype=torch.float32).unsqueeze(0)
test_sales = torch.tensor(daily_sales['Total Sales'].values[train_size + val_size:], dtype=torch.float32).unsqueeze(0)
# Define CNN + LSTM Model
class CNN_LSTM(nn.Module):
    def __init__(self, num_channels=3, lstm_hidden_size=50):
        super(CNN_LSTM, self).__init__()

        self.conv1 = nn.Conv2d(num_channels, 16, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)

        self.relu = nn.ReLU()
        self.maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dropout = nn.Dropout(p=0.5)

        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.lstm = nn.LSTM(input_size=1, hidden_size=lstm_hidden_size, num_layers=2, batch_first=True)
        self.fc = nn.Linear(lstm_hidden_size + 64, 7) 

    def forward(self, heatmap, sales_seq):
        # cnn input (heatmap) and ltsm input is the sales data
        #cnn processes heatmap 
        x = self.relu(self.conv1(heatmap))
        x = self.maxpool(x)
        x = self.dropout(x)

        x = self.relu(self.conv2(x))
        x = self.maxpool(x)
        x = self.dropout(x)

        x = self.relu(self.conv3(x))
        x = self.maxpool(x)
        x = self.dropout(x)

        x = self.global_pool(x).view(x.size(0), -1)

        #ltsm processes the sales data here 
        lstm_out, _ = self.lstm(sales_seq.unsqueeze(-1))
        lstm_out = lstm_out[:, -1, :].view(lstm_out.size(0), -1)

        # combined LTSM and CNN
        combined = torch.cat((x, lstm_out), dim=1)
        output = self.fc(combined)
        return torch.relu(output)

# Load heatmaps
paths = ["sales_heatmap.png", "monthly_sales.png", "holiday_heatmap.png"]

def load_heatmap(paths):
    # resized the heatmaps and grayscaled them 
    heatmaps = [cv2.imread(p, cv2.IMREAD_GRAYSCALE) for p in paths]
    heatmaps = [cv2.resize(h, (32, 32)).astype(np.float32) for h in heatmaps]
    heatmaps = [(h - np.mean(h)) / (np.std(h) + 1e-8) for h in heatmaps]
    heatmaps = np.stack(heatmaps, axis=0)
    return torch.tensor(heatmaps, dtype=torch.float32).unsqueeze(0)

X_heatmap = load_heatmap(paths)

# Model
model = CNN_LSTM(num_channels=3, lstm_hidden_size=120)  # Increase LSTM size (show the difference in the graphs)
optimizer = torch.optim.Adam(model.parameters(), lr=0.0003)  # Reduce learning rate 
criterion = nn.MSELoss()

# Define WMAPE function
def wmape(actual, predicted):
    return 100 * np.sum(np.abs(actual - predicted)) / np.sum(actual)


for epoch in range(50):  
    # Training step
    model.train()
    optimizer.zero_grad()
    
    # Forward pass
    outputs = model(X_heatmap, train_sales)  
    print("Output shape:", outputs.shape)
    loss = criterion(outputs, train_sales[:, -7:])  
    loss.backward()
    optimizer.step()
    print(f"Epoch [{epoch+1}/250] completed.,Loss: {loss.item():.4f}")

    # Evaluation (after training step)
    model.eval()
    with torch.no_grad():
        
        y_pred_train = model(X_heatmap, train_sales).detach().numpy()
        y_pred_test = model(X_heatmap, val_sales).detach().numpy()

        train_actual = train_sales[:, -7:].numpy().flatten()
        val_actual = val_sales[:, -7:].numpy().flatten()

        train_pred_tensor = torch.tensor(y_pred_train, dtype=torch.float32)
        val_pred_tensor = torch.tensor(y_pred_test, dtype=torch.float32)

        train_actual_tensor = torch.tensor(train_actual, dtype=torch.float32).view(1, -1)
        val_actual_tensor = torch.tensor(val_actual, dtype=torch.float32).view(1, -1)

        train_rmse = np.sqrt(criterion(train_pred_tensor, train_actual_tensor)).item()
        val_rmse = np.sqrt(criterion(val_pred_tensor, val_actual_tensor)).item()

        train_mape = mean_absolute_percentage_error(train_actual, y_pred_train.flatten()) * 100
        val_mape = mean_absolute_percentage_error(val_actual, y_pred_test.flatten()) * 100

        train_wmape = wmape(train_actual, y_pred_train.flatten())
        val_wmape = wmape(val_actual, y_pred_test.flatten())

        print(f"Epoch {epoch+1}: Train RMSE {train_rmse:.4f}, Validation RMSE {val_rmse:.4f}")
        print(f"Train MAPE: {train_mape:.2f}%, Validation MAPE: {val_mape:.2f}%")
        print(f"Train WMAPE: {train_wmape:.2f}%, Validation WMAPE: {val_wmape:.2f}%")
        


print("Training Completed")  


# Test Set Evaluation
with torch.no_grad():
    y_pred_test = model(X_heatmap, test_sales).detach().numpy()
    test_actual = test_sales[:, -7:].numpy().flatten()

    test_rmse = np.sqrt(criterion(torch.tensor(y_pred_test), torch.tensor(test_actual).view(1, -1))).item()
    test_mape = mean_absolute_percentage_error(test_actual, y_pred_test.flatten()) * 100
    test_wmape = wmape(test_actual, y_pred_test.flatten())

    print(f"Test RMSE: {test_rmse:.4f}")
    print(f"Test MAPE: {test_mape:.2f}%")
    print(f"Test WMAPE: {test_wmape:.2f}%")


# Predict Sales on Validation Set
predicted_val_sales = model(X_heatmap, val_sales).detach().numpy()
predicted_val_sales_rescaled= scaler.inverse_transform(predicted_val_sales)
actual_val_sales_rescaled = scaler.inverse_transform(val_sales.numpy().reshape(-1, 1)).flatten()

#plot validation predictions
plt.axvline(x=7, color='red', linestyle='dotted', label='Forecast Horizon')  
plt.plot(predicted_val_sales_rescaled.flatten(), label='Predicted Sales')
plt.plot(actual_val_sales_rescaled.flatten(), label='Actual Sales', linestyle='dashed')
plt.legend()
plt.title('Predicted vs Actual Sales (Validation Set)')
plt.xlabel('Day')
plt.ylabel('Sales')
plt.show()

# Plot test predictions
predicted_test_rescaled = scaler.inverse_transform(y_pred_test)
actual_test_rescaled = scaler.inverse_transform(test_sales.numpy().reshape(-1, 1)).flatten()

plt.figure()
plt.plot(predicted_test_rescaled.flatten(), label='Predicted Test Sales')
plt.plot(actual_test_rescaled.flatten(), label='Actual Test Sales', linestyle='dashed')
plt.title('Test Set: Predicted vs Actual Sales')
plt.legend()
plt.xlabel('Day')
plt.ylabel('Sales')
plt.show()

# Predict Future Sales (Next 7 Days)
future_sales_input = test_sales[:, -7:].clone()
predicted_future_sales = model(X_heatmap, future_sales_input).detach().numpy()
predicted_future_sales_rescaled = scaler.inverse_transform(predicted_future_sales)

# Plot future sales predictions
plt.figure()
plt.axvline(x=0, color='red', linestyle='dotted', label='Forecast Start')
plt.plot(predicted_future_sales_rescaled.flatten(), label='Predicted Future Sales', color='red')
plt.title('Predicted Sales for Next 7 Days')
plt.xlabel('Day')
plt.ylabel('Sales')
plt.legend()
plt.show()


# Print predicted future sales
print("Predicted Sales for Next 7 Days:", predicted_future_sales_rescaled.flatten())

# old code for validation set 
#changed so can use the test set to see how it sees unseen data


# the code should show the next days specifically
# ask if you think the sales prediction should show hourly 
# maybe I could add this to further works section? 
# ask about should the machine learning algorithm run only once per day 
#then run to get the other days (talk about this in the session on how it would be done to show the graph)

# explain research about the metrics to evaluate the model 
# Creating performance.csv file and driver.csv file ask if the steps and algorithms should be screenshoted in report
# same goes for the data cleaning bit and graph queries?

