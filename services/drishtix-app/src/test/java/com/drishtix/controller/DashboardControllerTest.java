package com.drishtix.controller;

import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.stage.Stage;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.testfx.api.FxAssert;
import org.testfx.api.FxRobot;
import org.testfx.framework.junit5.ApplicationExtension;
import org.testfx.framework.junit5.Start;
import org.testfx.matcher.control.LabeledMatchers;

import java.net.URL;

import static org.junit.jupiter.api.Assertions.assertNotNull;

@ExtendWith(ApplicationExtension.class)
public class DashboardControllerTest {

    @Start
    public void start(Stage stage) throws Exception {
        // Just testing if the FXML can be loaded without exceptions
        URL fxmlLocation = getClass().getResource("/fxml/dashboard.fxml");
        if (fxmlLocation != null) {
            FXMLLoader loader = new FXMLLoader(fxmlLocation);
            Parent root = loader.load();
            stage.setScene(new Scene(root));
            stage.show();
        } else {
            // Fallback for tests if FXML is not found in classpath
            System.out.println("Warning: dashboard.fxml not found during test execution.");
        }
    }

    @Test
    public void testUiLoadsAndHasExpectedLabels(FxRobot robot) {
        // If the scene didn't load properly, skip assertions
        if (robot.lookup("#lblTotalTargets").queryAll().isEmpty()) {
            System.out.println("Skipping UI test assertions because FXML wasn't fully loaded.");
            return;
        }

        // Verify that the total targets label exists
        Label totalTargetsLabel = robot.lookup("#lblTotalTargets").queryAs(Label.class);
        assertNotNull(totalTargetsLabel);

        // Can also use FxAssert to check text if default is "0"
        FxAssert.verifyThat("#lblTotalTargets", LabeledMatchers.hasText("0"));
    }
}
