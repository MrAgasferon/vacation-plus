package io.github.mragasferon.vacationplus.preview;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(VacationFilesPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
