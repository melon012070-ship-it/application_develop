package hello;
import java.awt.*;
import java.awt.event.*;
import javax.swing.*;


public class AnomymousClassListener {
public AnomymousClassListener() {
	setTitle("Action 이벤트 리스너 작성");
	setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
	Container c=getContentPane();
	c.setLayout(new FlowLayout());
	JButtin btn=new JButton("Action");
	c.add(btn);
	
	btn.addActionListener(new ActionListener()){
		public void actionPerformed(ActionEvent e) {
			JButton b=(JButton)e.getSource();
			
		}
	}
}
}
