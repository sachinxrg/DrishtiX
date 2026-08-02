package com.drishtix;
import com.drishtix.service.TelegramAlertService;
import com.drishtix.model.TargetRegistry;
import com.drishtix.model.TargetCategory;
import java.util.concurrent.CompletableFuture;

public class TestTelegram {
    public static void main(String[] args) throws Exception {
        System.out.println("Testing Telegram Alert...");
        TargetRegistry target = new TargetRegistry();
        target.setTargetId(1);
        target.setFullName("John Doe");
        target.setCategory(TargetCategory.CRIMINAL);
        target.setCaseNumber("FIR-1234");
        
        CompletableFuture<Boolean> future = TelegramAlertService.getInstance().sendDetectionAlert(
            target, "98.5%", null, "Camera 1", "Main Gate");
        boolean result = future.join();
        System.out.println("Result: " + result);
    }
}
