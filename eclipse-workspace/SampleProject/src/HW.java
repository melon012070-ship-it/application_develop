import java.util.Scanner;

class Calculate{
	static int add (int n1, int n2) {
		return n1 + n2;
		//	더하기
	}
	static int min (int n1, int n2) {
		return n1 - n2;
		//	빼기
	}
	static int mul (int n1, int n2) {
		return n1 * n2;
		//	곱하기
	}
	static int div (int n1, int n2) {
		return n1 / n2;
		// 나누기
	}
}

public class HW {
	public static void main(String[] args) {
		
		Scanner scan = new Scanner(System.in);
		
		Calculate calc = new Calculate();
		
		
		
		int num1, num2;
		
		char oper;
		
		String yn;
		
		System.out.println("only support +, -, *, /");
		
		num1 = scan.nextInt();
		
		
		oper = scan.next().charAt(0);
		
		num2 = scan.nextInt();
		
		
		switch (oper) {
			
			case '+':
				System.out.println("Answer -> "+num1+" + "+num2+" = "+Calculate.add(num1, num2));
			break;
			
			
			case '-':
				System.out.println("Answer -> "+num1+" - "+num2+" = "+Calculate.min(num1, num2));
			break;
			
			
			case '*':
				System.out.println("Answer -> "+num1+" * "+num2+" = "+Calculate.mul(num1, num2));
			break;
			
		
			case '/':
				System.out.println("Answer -> "+num1+" / "+num2+" = "+Calculate.div(num1, num2));
			break;
		}
		
	}
	}
