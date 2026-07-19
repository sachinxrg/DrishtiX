package com.drishtix;

/**
 * Non-Application launcher class for DrishtiX.
 * <p>
 * Required because the Maven Shade plugin cannot properly handle
 * a main class that extends javafx.application.Application.
 * This class delegates to DrishtiXApp.main().
 * </p>
 */
public class DrishtiXLauncher {

    public static void main(String[] args) {
        DrishtiXApp.main(args);
    }
}
